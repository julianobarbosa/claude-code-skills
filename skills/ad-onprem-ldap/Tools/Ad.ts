#!/usr/bin/env bun
/**
 * Ad - manage on-prem Active Directory users and groups over LDAPS. No PowerShell, no RSAT.
 *
 * Reads:  find-user, find-group, group-members, user-groups, user-status
 * Writes: add-member, remove-member, create-user, create-group, disable, enable, unlock,
 *         move, reset-password, set-group-scope
 *
 * Every write is a dry run unless --apply is passed. Output is JSON on stdout; errors are
 * JSON on stderr with a non-zero exit code. Run `bun Ad.ts help` for usage.
 */

import { appendFileSync, mkdirSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { parseArgs } from "node:util";
import { Attribute, Change, Client, InvalidCredentialsError } from "ldapts";
import {
  type AdConfig,
  NEW_USER_UAC,
  UAC_COMPUTED,
  asArray,
  asInt,
  asString,
  decodeGroupType,
  encodeGroupType,
  encodeUnicodePwd,
  escapeDnValue,
  escapeFilter,
  filetimeToIso,
  generatePassword,
  isAllowedOu,
  isDisabled,
  loadConfig,
  looksLikeDn,
  parseScope,
  rdnOf,
  scopeChangeProblem,
  setDisabled,
} from "./AdLib";

// =============================================================================
// Exit codes and errors
// =============================================================================

export const EXIT = { OK: 0, FAILED: 1, USAGE: 2, UNREACHABLE: 3, NOT_FOUND: 4, REFUSED: 5 } as const;

export class AdError extends Error {
  constructor(
    public code: number,
    message: string,
    public detail?: unknown,
  ) {
    super(message);
  }
}

// =============================================================================
// Dependencies (injected so tests can run without a domain controller)
// =============================================================================

type Entry = Record<string, string | string[] | Buffer | Buffer[]> & { dn: string };

/** The slice of ldapts' Client this tool uses. */
export interface LdapClient {
  search(base: string, opts: Record<string, unknown>): Promise<{ searchEntries: Entry[] }>;
  modify(dn: string, changes: Change | Change[]): Promise<void>;
  add(dn: string, entry: Record<string, string | string[] | Buffer>): Promise<void>;
  modifyDN(dn: string, newDN: string): Promise<void>;
  unbind(): Promise<void>;
}

export interface Session {
  client: LdapClient;
  dc: string;
}

export interface Deps {
  config: AdConfig;
  connect(): Promise<Session>;
  /** Store a new secret in the vault; returns an op:// reference. Never returns the secret. */
  storeSecret(vault: string, title: string, secret: string, notes: string): Promise<string>;
  audit(record: Record<string, unknown>): void;
  generatePassword(): string;
}

// =============================================================================
// Production wiring
// =============================================================================

async function opReadSecret(ref: string): Promise<string> {
  const p = Bun.spawn(["op", "read", "--no-newline", ref], { stdout: "pipe", stderr: "pipe" });
  const [out, code] = await Promise.all([new Response(p.stdout).text(), p.exited]);
  // stderr is deliberately discarded: only the exit code is reported.
  if (code !== 0 || out === "") throw new AdError(EXIT.FAILED, `op read failed (exit ${code}); check \`op whoami\``);
  return out;
}

async function opStoreSecret(vault: string, title: string, secret: string, notes: string): Promise<string> {
  // The secret travels on stdin as an item template, never in argv.
  const template = JSON.stringify({
    title,
    category: "PASSWORD",
    fields: [
      { id: "password", type: "CONCEALED", purpose: "PASSWORD", label: "password", value: secret },
      { id: "notesPlain", type: "STRING", purpose: "NOTES", label: "notesPlain", value: notes },
    ],
  });
  const p = Bun.spawn(["op", "item", "create", "--vault", vault, "--format", "json", "-"], {
    stdin: new Blob([template]),
    stdout: "pipe",
    stderr: "pipe",
  });
  const [out, code] = await Promise.all([new Response(p.stdout).text(), p.exited]);
  if (code !== 0) throw new AdError(EXIT.FAILED, `op item create failed (exit ${code}); AD was not changed`);
  const id = (JSON.parse(out) as { id?: string }).id;
  if (!id) throw new AdError(EXIT.FAILED, "op item create returned no id; AD was not changed");
  return `op://${vault}/${id}/password`;
}

const NETWORK_ERROR = /ECONNREFUSED|ETIMEDOUT|ENOTFOUND|EHOSTUNREACH|ENETUNREACH|EAI_AGAIN|timeout|socket/i;

function productionDeps(config: AdConfig): Deps {
  return {
    config,
    async connect() {
      let ca: Buffer;
      try {
        ca = readFileSync(config.caBundle);
      } catch {
        throw new AdError(EXIT.USAGE, `CA bundle not readable: ${config.caBundle}`);
      }
      const password = await opReadSecret(config.passwordRef);
      const tried: string[] = [];
      for (const dc of config.dcs) {
        const client = new Client({
          url: `ldaps://${dc}:${config.port}`,
          tlsOptions: { ca: [ca], minVersion: "TLSv1.2" },
          timeout: 20000,
          connectTimeout: 5000,
        });
        try {
          await client.bind(config.bindUpn, password);
          return { client: client as unknown as LdapClient, dc };
        } catch (e) {
          await client.unbind().catch(() => {});
          // A bad password is retried on no other DC: each attempt counts toward lockout.
          if (e instanceof InvalidCredentialsError) throw new AdError(EXIT.FAILED, `bind rejected by ${dc}: invalid credentials`);
          const msg = e instanceof Error ? e.message : String(e);
          if (!NETWORK_ERROR.test(msg)) throw new AdError(EXIT.FAILED, `bind to ${dc} failed: ${msg}`);
          tried.push(`${dc}: ${msg}`);
        }
      }
      throw new AdError(EXIT.UNREACHABLE, "no domain controller reachable over LDAPS (VPN connected? DNS resolving the domain?)", tried);
    },
    storeSecret: opStoreSecret,
    audit(record) {
      const path = join(homedir(), ".local", "state", "ad-onprem", "audit.jsonl");
      mkdirSync(dirname(path), { recursive: true });
      appendFileSync(path, JSON.stringify(record) + "\n", { mode: 0o600 });
    },
    generatePassword: () => generatePassword(),
  };
}

// =============================================================================
// Lookups
// =============================================================================

const USER_ATTRS = [
  "sAMAccountName",
  "userPrincipalName",
  "displayName",
  "mail",
  "userAccountControl",
  "lockoutTime",
  "pwdLastSet",
  "lastLogonTimestamp",
  "whenCreated",
  "adminCount",
  "primaryGroupID",
];
const GROUP_ATTRS = ["sAMAccountName", "cn", "groupType", "description", "managedBy", "adminCount"];

async function findOne(s: Session, base: string, filter: string, attributes: string[], what: string, id: string): Promise<Entry> {
  const { searchEntries } = await s.client.search(base, { scope: "sub", filter, attributes, sizeLimit: 10 });
  if (searchEntries.length === 0) throw new AdError(EXIT.NOT_FOUND, `${what} not found: ${id}`);
  if (searchEntries.length > 1) throw new AdError(EXIT.NOT_FOUND, `${what} is ambiguous: ${id}`, searchEntries.map((e) => e.dn));
  return searchEntries[0];
}

async function byDn(s: Session, dn: string, attributes: string[], what: string): Promise<Entry> {
  try {
    const { searchEntries } = await s.client.search(dn, { scope: "base", filter: "(objectClass=*)", attributes });
    if (searchEntries[0]) return searchEntries[0];
  } catch {
    // fall through to not-found
  }
  throw new AdError(EXIT.NOT_FOUND, `${what} not found: ${dn}`);
}

function idFilter(id: string): string {
  const v = escapeFilter(id);
  return `(|(sAMAccountName=${v})(userPrincipalName=${v}))`;
}

export function resolveUser(s: Session, base: string, id: string, attrs = USER_ATTRS): Promise<Entry> {
  if (looksLikeDn(id)) return byDn(s, id, attrs, "user");
  return findOne(s, base, `(&(objectCategory=person)(objectClass=user)${idFilter(id)})`, attrs, "user", id);
}

export function resolveGroup(s: Session, base: string, id: string, attrs = GROUP_ATTRS): Promise<Entry> {
  if (looksLikeDn(id)) return byDn(s, id, attrs, "group");
  const v = escapeFilter(id);
  return findOne(s, base, `(&(objectClass=group)(|(sAMAccountName=${v})(cn=${v})))`, attrs, "group", id);
}

/** A group member can be a user, a group, a contact or a computer. */
function resolvePrincipal(s: Session, base: string, id: string): Promise<Entry> {
  const attrs = ["sAMAccountName", "objectClass", "adminCount"];
  if (looksLikeDn(id)) return byDn(s, id, attrs, "principal");
  const v = escapeFilter(id);
  const filter = `(|(sAMAccountName=${v})(sAMAccountName=${v}$)(userPrincipalName=${v})(&(objectClass=group)(cn=${v})))`;
  return findOne(s, base, filter, attrs, "principal", id);
}

/** Direct members, using ranged retrieval so groups past the server's MaxValRange are complete. */
export async function directMembers(s: Session, groupDn: string): Promise<string[]> {
  const out: string[] = [];
  let start = 0;
  for (;;) {
    const { searchEntries } = await s.client.search(groupDn, { scope: "base", filter: "(objectClass=*)", attributes: [`member;range=${start}-*`] });
    const e = searchEntries[0];
    if (!e) break;
    const key = Object.keys(e).find((k) => k.toLowerCase().startsWith("member;range="));
    if (!key) {
      out.push(...asArray(e.member));
      break;
    }
    out.push(...asArray(e[key]));
    const end = key.slice(key.lastIndexOf("-") + 1);
    if (end === "*") break;
    start = Number(end) + 1;
  }
  return out;
}

async function isDirectMember(s: Session, groupDn: string, memberDn: string): Promise<boolean> {
  const { searchEntries } = await s.client.search(groupDn, { scope: "base", filter: `(member=${escapeFilter(memberDn)})`, attributes: ["1.1"] });
  return searchEntries.length > 0;
}

function userView(e: Entry) {
  const uac = asInt(e.userAccountControl) ?? 0;
  return {
    dn: e.dn,
    sAMAccountName: asString(e.sAMAccountName),
    userPrincipalName: asString(e.userPrincipalName),
    displayName: asString(e.displayName),
    mail: asString(e.mail),
    enabled: !isDisabled(uac),
    userAccountControl: uac,
    lockoutTime: filetimeToIso(asString(e.lockoutTime)),
    pwdLastSet: filetimeToIso(asString(e.pwdLastSet)),
    lastLogonTimestamp: filetimeToIso(asString(e.lastLogonTimestamp)),
    whenCreated: asString(e.whenCreated),
    protected: asInt(e.adminCount) === 1,
  };
}

function groupView(e: Entry) {
  const gt = asInt(e.groupType) ?? 0;
  return {
    dn: e.dn,
    sAMAccountName: asString(e.sAMAccountName),
    ...decodeGroupType(gt),
    groupType: gt,
    description: asString(e.description),
    managedBy: asString(e.managedBy),
    protected: asInt(e.adminCount) === 1,
  };
}

// =============================================================================
// Write gate: dry run by default, --apply to execute, before/after from the same DC
// =============================================================================

interface WritePlan {
  op: string;
  dn: string;
  changes: Record<string, unknown>;
  protected?: boolean;
  before: unknown;
  noop?: string;
  exec(): Promise<void>;
  after(): Promise<unknown>;
}

async function write(deps: Deps, s: Session, flags: Flags, plan: WritePlan) {
  const base = { op: plan.op, dn: plan.dn, dc: s.dc, changes: plan.changes, before: plan.before };
  if (plan.noop) return { mode: "noop", reason: plan.noop, ...base };
  if (plan.protected && !flags["allow-protected"]) {
    throw new AdError(EXIT.REFUSED, `${plan.dn} is AdminSDHolder-protected (adminCount=1); pass --allow-protected if this is intended`);
  }
  if (!flags.apply) return { mode: "dry-run", hint: "re-run with --apply to execute", ...base };

  const ts = new Date().toISOString();
  try {
    await plan.exec();
  } catch (e) {
    deps.audit({ ts, ...base, before: undefined, result: "error", error: e instanceof Error ? e.message : String(e) });
    throw e;
  }
  const after = await plan.after();
  deps.audit({ ts, op: plan.op, dn: plan.dn, dc: s.dc, bindUpn: deps.config.bindUpn, changes: plan.changes, result: "applied" });
  return { mode: "applied", ...base, after };
}

function assertAllowedOu(deps: Deps, ou: string) {
  if (!isAllowedOu(ou, deps.config.writeOuAllowlist)) {
    throw new AdError(EXIT.REFUSED, `OU is not in writeOuAllowlist: ${ou}`, deps.config.writeOuAllowlist);
  }
}

// =============================================================================
// Commands
// =============================================================================

type Flags = Record<string, string | boolean | undefined>;
type Handler = (deps: Deps, s: Session, args: string[], flags: Flags) => Promise<unknown>;

function need(args: string[], n: number, usage: string): void {
  if (args.length < n) throw new AdError(EXIT.USAGE, `usage: ${usage}`);
}

function flagStr(flags: Flags, name: string, required = false): string | undefined {
  const v = flags[name];
  if (typeof v === "string" && v !== "") return v;
  if (required) throw new AdError(EXIT.USAGE, `--${name} is required`);
  return undefined;
}

async function membership(op: "add" | "delete", deps: Deps, s: Session, args: string[], flags: Flags) {
  const name = op === "add" ? "add-member" : "remove-member";
  need(args, 2, `${name} <group> <member> [<member>...] [--apply]`);
  const base = deps.config.baseDn;
  const group = await resolveGroup(s, base, args[0]);
  const results = [];
  for (const id of args.slice(1)) {
    const member = await resolvePrincipal(s, base, id);
    const was = await isDirectMember(s, group.dn, member.dn);
    results.push(
      await write(deps, s, flags, {
        op: name,
        dn: group.dn,
        changes: { member: { [op]: member.dn } },
        protected: asInt(group.adminCount) === 1,
        before: { isDirectMember: was },
        noop: op === "add" && was ? "already a direct member" : op === "delete" && !was ? "not a direct member" : undefined,
        exec: () => s.client.modify(group.dn, new Change({ operation: op, modification: new Attribute({ type: "member", values: [member.dn] }) })),
        after: async () => ({ isDirectMember: await isDirectMember(s, group.dn, member.dn) }),
      }),
    );
  }
  return results.length === 1 ? results[0] : results;
}

async function toggleEnabled(disable: boolean, deps: Deps, s: Session, args: string[], flags: Flags) {
  need(args, 1, `${disable ? "disable" : "enable"} <user> [--apply]`);
  const u = await resolveUser(s, deps.config.baseDn, args[0]);
  const uac = asInt(u.userAccountControl) ?? 0;
  const next = setDisabled(uac, disable);
  return write(deps, s, flags, {
    op: disable ? "disable" : "enable",
    dn: u.dn,
    changes: { userAccountControl: { from: uac, to: next } },
    protected: asInt(u.adminCount) === 1,
    before: { enabled: !isDisabled(uac) },
    noop: next === uac ? `already ${disable ? "disabled" : "enabled"}` : undefined,
    exec: () => s.client.modify(u.dn, new Change({ operation: "replace", modification: new Attribute({ type: "userAccountControl", values: [String(next)] }) })),
    after: async () => ({ enabled: !isDisabled(asInt((await resolveUser(s, deps.config.baseDn, u.dn)).userAccountControl) ?? 0) }),
  });
}

const STATUS_ATTRS = [...USER_ATTRS, "msDS-User-Account-Control-Computed", "badPwdCount", "accountExpires"];

async function userStatus(deps: Deps, s: Session, id: string) {
  // The computed attribute is only returned on a base-scope read of the object itself.
  const found = await resolveUser(s, deps.config.baseDn, id, ["1.1"]);
  const e = await byDn(s, found.dn, STATUS_ATTRS, "user");
  const computed = asInt(e["msDS-User-Account-Control-Computed"]) ?? 0;
  return {
    ...userView(e),
    locked: (computed & UAC_COMPUTED.LOCKOUT) !== 0,
    passwordExpired: (computed & UAC_COMPUTED.PASSWORD_EXPIRED) !== 0,
    badPwdCount: asInt(e.badPwdCount),
    accountExpires: filetimeToIso(asString(e.accountExpires)),
  };
}

export const COMMANDS: Record<string, { usage: string; write: boolean; run: Handler }> = {
  "find-user": {
    usage: "find-user <sam|upn|dn> | find-user --prefix <text>",
    write: false,
    async run(deps, s, args, flags) {
      const prefix = flagStr(flags, "prefix");
      if (prefix) {
        const v = escapeFilter(prefix);
        const filter = `(&(objectCategory=person)(objectClass=user)(|(sAMAccountName=${v}*)(displayName=${v}*)(mail=${v}*)))`;
        const { searchEntries } = await s.client.search(deps.config.baseDn, { scope: "sub", filter, attributes: USER_ATTRS, sizeLimit: 50 });
        return searchEntries.map(userView);
      }
      need(args, 1, this.usage);
      return userView(await resolveUser(s, deps.config.baseDn, args[0]));
    },
  },
  "find-group": {
    usage: "find-group <sam|cn|dn>",
    write: false,
    async run(deps, s, args) {
      need(args, 1, this.usage);
      const g = await resolveGroup(s, deps.config.baseDn, args[0]);
      return { ...groupView(g), directMemberCount: (await directMembers(s, g.dn)).length };
    },
  },
  "group-members": {
    usage: "group-members <group> [--recursive]",
    write: false,
    async run(deps, s, args, flags) {
      need(args, 1, this.usage);
      const g = await resolveGroup(s, deps.config.baseDn, args[0]);
      if (!flags.recursive) {
        const dns = await directMembers(s, g.dn);
        return { group: g.dn, recursive: false, count: dns.length, members: dns };
      }
      // LDAP_MATCHING_RULE_IN_CHAIN walks nested groups server-side.
      const { searchEntries } = await s.client.search(deps.config.baseDn, {
        scope: "sub",
        filter: `(memberOf:1.2.840.113556.1.4.1941:=${escapeFilter(g.dn)})`,
        attributes: ["sAMAccountName", "objectClass"],
        paged: { pageSize: 500 },
      });
      const members = searchEntries.map((e) => ({ dn: e.dn, sAMAccountName: asString(e.sAMAccountName), objectClass: asArray(e.objectClass).at(-1) }));
      return { group: g.dn, recursive: true, count: members.length, members };
    },
  },
  "user-groups": {
    usage: "user-groups <user> [--recursive]",
    write: false,
    async run(deps, s, args, flags) {
      need(args, 1, this.usage);
      const u = await resolveUser(s, deps.config.baseDn, args[0], ["memberOf", "primaryGroupID"]);
      const note = "the primary group (primaryGroupID, usually Domain Users) is not listed in memberOf";
      if (!flags.recursive) {
        const groups = asArray(u.memberOf);
        return { user: u.dn, recursive: false, count: groups.length, groups, primaryGroupID: asInt(u.primaryGroupID), note };
      }
      const { searchEntries } = await s.client.search(deps.config.baseDn, {
        scope: "sub",
        filter: `(&(objectClass=group)(member:1.2.840.113556.1.4.1941:=${escapeFilter(u.dn)}))`,
        attributes: ["1.1"],
        paged: { pageSize: 500 },
      });
      const groups = searchEntries.map((e) => e.dn);
      return { user: u.dn, recursive: true, count: groups.length, groups, primaryGroupID: asInt(u.primaryGroupID), note };
    },
  },
  "user-status": {
    usage: "user-status <user>",
    write: false,
    async run(deps, s, args) {
      need(args, 1, this.usage);
      return userStatus(deps, s, args[0]);
    },
  },

  "add-member": { usage: "add-member <group> <member>... [--apply]", write: true, run: (d, s, a, f) => membership("add", d, s, a, f) },
  "remove-member": { usage: "remove-member <group> <member>... [--apply]", write: true, run: (d, s, a, f) => membership("delete", d, s, a, f) },
  disable: { usage: "disable <user> [--apply]", write: true, run: (d, s, a, f) => toggleEnabled(true, d, s, a, f) },
  enable: { usage: "enable <user> [--apply]", write: true, run: (d, s, a, f) => toggleEnabled(false, d, s, a, f) },

  unlock: {
    usage: "unlock <user> [--apply]",
    write: true,
    async run(deps, s, args, flags) {
      need(args, 1, this.usage);
      const st = await userStatus(deps, s, args[0]);
      return write(deps, s, flags, {
        op: "unlock",
        dn: st.dn,
        changes: { lockoutTime: { to: "0" } },
        protected: st.protected,
        before: { locked: st.locked, lockoutTime: st.lockoutTime },
        noop: st.locked ? undefined : "account is not locked",
        exec: () => s.client.modify(st.dn, new Change({ operation: "replace", modification: new Attribute({ type: "lockoutTime", values: ["0"] }) })),
        after: async () => ({ locked: (await userStatus(deps, s, st.dn)).locked }),
      });
    },
  },

  move: {
    usage: "move <user|group|dn> --to <ou-dn> [--apply]",
    write: true,
    async run(deps, s, args, flags) {
      need(args, 1, this.usage);
      const to = flagStr(flags, "to", true)!;
      assertAllowedOu(deps, to);
      const obj = await resolvePrincipal(s, deps.config.baseDn, args[0]);
      const newDn = `${rdnOf(obj.dn)},${to}`;
      return write(deps, s, flags, {
        op: "move",
        dn: obj.dn,
        changes: { dn: { from: obj.dn, to: newDn } },
        protected: asInt(obj.adminCount) === 1,
        before: { dn: obj.dn },
        exec: () => s.client.modifyDN(obj.dn, newDn),
        after: async () => ({ dn: (await byDn(s, newDn, ["1.1"], "moved object")).dn }),
      });
    },
  },

  "reset-password": {
    usage: "reset-password <user> [--must-change] [--vault <name>] [--apply]",
    write: true,
    async run(deps, s, args, flags) {
      need(args, 1, this.usage);
      const vault = flagStr(flags, "vault") ?? deps.config.passwordVault;
      if (!vault) throw new AdError(EXIT.USAGE, "no vault: set passwordVault in config or pass --vault");
      const u = await resolveUser(s, deps.config.baseDn, args[0]);
      const mustChange = flags["must-change"] === true;
      let ref = "(created on --apply)";
      return write(deps, s, flags, {
        op: "reset-password",
        dn: u.dn,
        changes: { unicodePwd: "<generated, stored in vault>", vault, ...(mustChange ? { pwdLastSet: { to: "0" } } : {}) },
        protected: asInt(u.adminCount) === 1,
        before: { pwdLastSet: filetimeToIso(asString(u.pwdLastSet)) },
        async exec() {
          const password = deps.generatePassword();
          // Vault first: if AD then fails, the old password still works and the item is just unused.
          ref = await deps.storeSecret(vault, `AD ${asString(u.sAMAccountName)} ${new Date().toISOString().slice(0, 10)}`, password, u.dn);
          const changes = [new Change({ operation: "replace", modification: new Attribute({ type: "unicodePwd", values: [encodeUnicodePwd(password)] }) })];
          if (mustChange) changes.push(new Change({ operation: "replace", modification: new Attribute({ type: "pwdLastSet", values: ["0"] }) }));
          try {
            await s.client.modify(u.dn, changes);
          } catch (e) {
            throw new AdError(EXIT.FAILED, `AD rejected the reset (${e instanceof Error ? e.message : e}); vault item ${ref} holds an unused password`);
          }
        },
        after: async () => ({ passwordRef: ref, pwdLastSet: filetimeToIso(asString((await resolveUser(s, deps.config.baseDn, u.dn)).pwdLastSet)) }),
      });
    },
  },

  "create-user": {
    usage: "create-user <sam> --ou <ou-dn> --given <first> --sn <last> [--display <name>] [--upn <upn>] [--apply]",
    write: true,
    async run(deps, s, args, flags) {
      need(args, 1, this.usage);
      const sam = args[0];
      const ou = flagStr(flags, "ou", true)!;
      assertAllowedOu(deps, ou);
      const given = flagStr(flags, "given", true)!;
      const sn = flagStr(flags, "sn", true)!;
      const display = flagStr(flags, "display") ?? `${given} ${sn}`;
      const upn = flagStr(flags, "upn") ?? `${sam}@${deps.config.domain}`;
      const dn = `CN=${escapeDnValue(display)},${ou}`;
      const { searchEntries: clash } = await s.client.search(deps.config.baseDn, {
        scope: "sub",
        filter: `(|(sAMAccountName=${escapeFilter(sam)})(userPrincipalName=${escapeFilter(upn)}))`,
        attributes: ["1.1"],
      });
      if (clash.length) throw new AdError(EXIT.REFUSED, `sAMAccountName or UPN already in use`, clash.map((e) => e.dn));
      const entry = {
        objectClass: ["top", "person", "organizationalPerson", "user"],
        sAMAccountName: sam,
        userPrincipalName: upn,
        givenName: given,
        sn,
        displayName: display,
        userAccountControl: String(NEW_USER_UAC),
      };
      return write(deps, s, flags, {
        op: "create-user",
        dn,
        changes: { add: entry, note: "created disabled; run reset-password then enable" },
        before: null,
        exec: () => s.client.add(dn, entry),
        after: async () => userView(await byDn(s, dn, USER_ATTRS, "created user")),
      });
    },
  },

  "create-group": {
    usage: "create-group <sam> --ou <ou-dn> [--scope global|domainlocal|universal] [--type security|distribution] [--description <text>] [--apply]",
    write: true,
    async run(deps, s, args, flags) {
      need(args, 1, this.usage);
      const sam = args[0];
      const ou = flagStr(flags, "ou", true)!;
      assertAllowedOu(deps, ou);
      const scope = parseScope(flagStr(flags, "scope") ?? "global");
      if (!scope) throw new AdError(EXIT.USAGE, "--scope must be global, domainlocal or universal");
      const type = flagStr(flags, "type") ?? "security";
      if (type !== "security" && type !== "distribution") throw new AdError(EXIT.USAGE, "--type must be security or distribution");
      const dn = `CN=${escapeDnValue(sam)},${ou}`;
      const { searchEntries: clash } = await s.client.search(deps.config.baseDn, { scope: "sub", filter: `(sAMAccountName=${escapeFilter(sam)})`, attributes: ["1.1"] });
      if (clash.length) throw new AdError(EXIT.REFUSED, "sAMAccountName already in use", clash.map((e) => e.dn));
      const entry: Record<string, string | string[]> = { objectClass: ["top", "group"], sAMAccountName: sam, groupType: String(encodeGroupType(scope, type)) };
      const description = flagStr(flags, "description");
      if (description) entry.description = description;
      return write(deps, s, flags, {
        op: "create-group",
        dn,
        changes: { add: entry, scope, type },
        before: null,
        exec: () => s.client.add(dn, entry),
        after: async () => groupView(await byDn(s, dn, GROUP_ATTRS, "created group")),
      });
    },
  },

  "set-group-scope": {
    usage: "set-group-scope <group> --scope global|domainlocal|universal [--apply]",
    write: true,
    async run(deps, s, args, flags) {
      need(args, 1, this.usage);
      const to = parseScope(flagStr(flags, "scope", true));
      if (!to) throw new AdError(EXIT.USAGE, "--scope must be global, domainlocal or universal");
      const g = await resolveGroup(s, deps.config.baseDn, args[0]);
      const cur = decodeGroupType(asInt(g.groupType) ?? 0);
      if (cur.scope === "unknown") throw new AdError(EXIT.FAILED, `unrecognized groupType on ${g.dn}`);
      const problem = scopeChangeProblem(cur.scope, to);
      if (problem) throw new AdError(EXIT.REFUSED, problem);
      const next = encodeGroupType(to, cur.kind);
      return write(deps, s, flags, {
        op: "set-group-scope",
        dn: g.dn,
        changes: { groupType: { from: asInt(g.groupType), to: next }, scope: { from: cur.scope, to } },
        protected: asInt(g.adminCount) === 1,
        before: { scope: cur.scope },
        noop: cur.scope === to ? `already ${to}` : undefined,
        exec: () => s.client.modify(g.dn, new Change({ operation: "replace", modification: new Attribute({ type: "groupType", values: [String(next)] }) })),
        after: async () => ({ scope: decodeGroupType(asInt((await resolveGroup(s, deps.config.baseDn, g.dn)).groupType) ?? 0).scope }),
      });
    },
  },
};

// =============================================================================
// Entry point
// =============================================================================

const OPTIONS = {
  apply: { type: "boolean" },
  recursive: { type: "boolean" },
  "must-change": { type: "boolean" },
  "allow-protected": { type: "boolean" },
  prefix: { type: "string" },
  ou: { type: "string" },
  to: { type: "string" },
  scope: { type: "string" },
  type: { type: "string" },
  given: { type: "string" },
  sn: { type: "string" },
  display: { type: "string" },
  upn: { type: "string" },
  description: { type: "string" },
  vault: { type: "string" },
  config: { type: "string" },
} as const;

function helpText(): string {
  return ["Usage: bun Ad.ts <command> [args] [flags]", "", ...Object.values(COMMANDS).map((c) => `  ${c.usage}`), "", "Writes are dry runs unless --apply is given."].join("\n");
}

export async function main(argv: string[], makeDeps: (configPath?: string) => Deps = (p) => productionDeps(loadConfig(p))): Promise<{ code: number; out?: unknown; err?: unknown }> {
  let parsed;
  try {
    parsed = parseArgs({ args: argv, options: OPTIONS, allowPositionals: true, strict: true });
  } catch (e) {
    return { code: EXIT.USAGE, err: { error: e instanceof Error ? e.message : String(e) } };
  }
  const [name, ...args] = parsed.positionals;
  if (!name || name === "help") return { code: name ? EXIT.OK : EXIT.USAGE, out: helpText() };
  const cmd = COMMANDS[name];
  if (!cmd) return { code: EXIT.USAGE, err: { error: `unknown command: ${name}`, help: helpText() } };

  let session: Session | undefined;
  try {
    const deps = makeDeps(parsed.values.config);
    session = await deps.connect();
    return { code: EXIT.OK, out: await cmd.run(deps, session, args, parsed.values) };
  } catch (e) {
    if (e instanceof AdError) return { code: e.code, err: { error: e.message, detail: e.detail } };
    return { code: EXIT.FAILED, err: { error: e instanceof Error ? `${e.constructor.name}: ${e.message}` : String(e) } };
  } finally {
    await session?.client.unbind().catch(() => {});
  }
}

if (import.meta.main) {
  const r = await main(process.argv.slice(2));
  if (r.out !== undefined) console.log(typeof r.out === "string" ? r.out : JSON.stringify(r.out, null, 2));
  if (r.err !== undefined) console.error(JSON.stringify(r.err, null, 2));
  process.exit(r.code);
}
