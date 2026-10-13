import { describe, expect, test } from "bun:test";
import { type Change, EqualityFilter, NoSuchObjectError } from "ldapts";
import { type Deps, EXIT, type LdapClient, main } from "./Ad";
import {
  NEW_USER_UAC,
  decodeGroupType,
  encodeGroupType,
  encodeUnicodePwd,
  escapeDnValue,
  escapeFilter,
  filetimeToIso,
  generatePassword,
  isAllowedOu,
  isDisabled,
  isDnUnder,
  parseConfig,
  scopeChangeProblem,
  setDisabled,
  splitDn,
} from "./AdLib";

// =============================================================================
// Pure helpers
// =============================================================================

describe("escaping", () => {
  test("filter values escape the RFC 4515 specials", () => {
    expect(escapeFilter("a*(b)\\")).toBe("a\\2a\\28b\\29\\5c");
    expect(escapeFilter("CN=Doe\\, Jane,DC=x")).toBe("CN=Doe\\5c, Jane,DC=x");
  });

  test("DN values escape the RFC 4514 specials and edge spaces", () => {
    expect(escapeDnValue("Doe, Jane")).toBe("Doe\\, Jane");
    expect(escapeDnValue("#ops")).toBe("\\#ops");
    expect(escapeDnValue("a+b=c")).toBe("a\\+b\\=c");
    expect(escapeDnValue("trailing ")).toBe("trailing\\ ");
    // A raw value ending in backslash + space: both are escaped.
    expect(escapeDnValue("a\\ ")).toBe("a\\\\\\ ");
  });

  test("splitDn keeps escaped commas inside one RDN", () => {
    expect(splitDn("CN=Doe\\, Jane, OU=Users,DC=x")).toEqual(["CN=Doe\\, Jane", "OU=Users", "DC=x"]);
  });

  test("splitDn keeps an escaped trailing space", () => {
    expect(splitDn("CN=a\\ ,DC=x")).toEqual(["CN=a\\ ", "DC=x"]);
    expect(splitDn("CN=a\\  , DC=x ")).toEqual(["CN=a\\ ", "DC=x"]);
  });
});

describe("OU containment", () => {
  const allow = ["OU=Managed,DC=corp,DC=example,DC=com"];
  test("accepts the OU itself and anything beneath it, ignoring case and spacing", () => {
    expect(isAllowedOu("ou=managed, dc=corp,dc=example,dc=com", allow)).toBe(true);
    expect(isAllowedOu("OU=Sub,OU=Managed,DC=corp,DC=example,DC=com", allow)).toBe(true);
  });
  test("rejects siblings that merely share a suffix string", () => {
    expect(isAllowedOu("OU=UnManaged,DC=corp,DC=example,DC=com", allow)).toBe(false);
    expect(isDnUnder("OU=XManaged,DC=corp,DC=example,DC=com", allow[0])).toBe(false);
    expect(isAllowedOu("DC=corp,DC=example,DC=com", allow)).toBe(false);
  });
});

describe("userAccountControl", () => {
  test("disable and enable flip only bit 0x2", () => {
    expect(setDisabled(0x200, true)).toBe(0x202);
    expect(setDisabled(0x10202, false)).toBe(0x10200);
    expect(isDisabled(0x202)).toBe(true);
    expect(NEW_USER_UAC).toBe(514);
  });
});

describe("groupType", () => {
  test("encodes as AD's signed 32-bit value", () => {
    expect(encodeGroupType("global", "security")).toBe(-2147483646);
    expect(encodeGroupType("domainlocal", "security")).toBe(-2147483644);
    expect(encodeGroupType("universal", "distribution")).toBe(8);
  });
  test("round-trips", () => {
    for (const scope of ["global", "domainlocal", "universal"] as const)
      for (const kind of ["security", "distribution"] as const) expect(decodeGroupType(encodeGroupType(scope, kind))).toEqual({ scope, kind });
  });
  test("scope changes must pass through universal", () => {
    expect(scopeChangeProblem("global", "universal")).toBeNull();
    expect(scopeChangeProblem("universal", "domainlocal")).toBeNull();
    expect(scopeChangeProblem("global", "domainlocal")).toContain("universal first");
    expect(scopeChangeProblem("domainlocal", "global")).toContain("universal first");
  });
});

describe("passwords and time", () => {
  test("unicodePwd is the quoted password in UTF-16LE", () => {
    expect(encodeUnicodePwd("ab").toString("hex")).toBe("220061006200" + "2200");
  });
  test("generated passwords always carry all four character classes", () => {
    for (let i = 0; i < 300; i++) {
      const pw = generatePassword(24);
      expect(pw).toHaveLength(24);
      expect(pw).toMatch(/[A-Z]/);
      expect(pw).toMatch(/[a-z]/);
      expect(pw).toMatch(/[0-9]/);
      expect(pw).toMatch(/[^A-Za-z0-9]/);
      expect(pw).not.toContain('"');
    }
  });
  test("FILETIME converts, and 0 / never mean null", () => {
    expect(filetimeToIso("116444736000000000")).toBe("1970-01-01T00:00:00.000Z");
    expect(filetimeToIso("0")).toBeNull();
    expect(filetimeToIso("9223372036854775807")).toBeNull();
  });
});

const VALID = {
  domain: "corp.example.com",
  baseDn: "DC=corp,DC=example,DC=com",
  dcs: ["dc01.corp.example.com"],
  bindUpn: "admin@corp.example.com",
  passwordRef: "op://Vault/item/password",
  caBundle: "~/ca.pem",
  writeOuAllowlist: ["OU=Managed,DC=corp,DC=example,DC=com"],
  passwordVault: "Vault",
};

describe("config", () => {
  test("accepts a valid config and defaults to LDAPS", () => {
    const c = parseConfig(VALID);
    expect(c.port).toBe(636);
    expect(c.caBundle.endsWith("/ca.pem")).toBe(true);
    expect(c.caBundle.startsWith("~")).toBe(false);
  });
  test("rejects plain LDAP, non-op secrets and OUs outside the base", () => {
    expect(() => parseConfig({ ...VALID, port: 389 })).toThrow(/LDAPS/);
    expect(() => parseConfig({ ...VALID, passwordRef: "hunter2" })).toThrow(/op:\/\//);
    expect(() => parseConfig({ ...VALID, writeOuAllowlist: ["OU=X,DC=other,DC=com"] })).toThrow(/outside baseDn/);
    expect(() => parseConfig({})).toThrow(/domain/);
  });
});

// =============================================================================
// CLI against an in-memory directory
// =============================================================================

type FakeEntry = Record<string, string | string[] | Buffer> & { dn: string };

const BASE = VALID.baseDn;
const GROUP_DN = "CN=App Readers,OU=Managed,DC=corp,DC=example,DC=com";
const JANE_DN = "CN=Jane Doe,OU=Managed,DC=corp,DC=example,DC=com";
const ADMIN_DN = "CN=Root Admin,OU=Admins,DC=corp,DC=example,DC=com";

function directory(): FakeEntry[] {
  return [
    { dn: GROUP_DN, objectClass: ["top", "group"], sAMAccountName: "app-readers", cn: "App Readers", groupType: String(encodeGroupType("global", "security")), member: [] },
    { dn: JANE_DN, objectClass: ["top", "person", "organizationalPerson", "user"], sAMAccountName: "jdoe", userPrincipalName: "jdoe@corp.example.com", userAccountControl: "512" },
    { dn: ADMIN_DN, objectClass: ["top", "person", "organizationalPerson", "user"], sAMAccountName: "radmin", userAccountControl: "512", adminCount: "1" },
  ];
}

const unescape = (v: string) => v.replace(/\\([0-9a-f]{2})/gi, (_, h) => String.fromCharCode(Number.parseInt(h, 16)));
const same = (a: string, b: string) => a.toLowerCase() === b.toLowerCase();

/** Just enough filter matching for the shapes Ad.ts sends. */
interface FakeOpts {
  memberPages?: string[][];
  /** Runs inside modify, before it fails: simulates another writer getting there first. */
  race?: (entries: FakeEntry[]) => void;
  /** Base reads throw a non-NoSuchObject error once a write has happened. */
  breakReadsAfterWrite?: boolean;
}

function fakeClient(entries: FakeEntry[], log: { op: string; dn: string; arg: unknown }[], o: FakeOpts = {}): LdapClient {
  const memberPages = o.memberPages;
  return {
    async search(base, opts) {
      if (opts.filter instanceof EqualityFilter && Buffer.isBuffer(opts.filter.value)) {
        const want = opts.filter.value;
        return { searchEntries: entries.filter((e) => Buffer.isBuffer(e.objectSid) && e.objectSid.equals(want)) };
      }
      const filter = String(opts.filter ?? "(objectClass=*)");
      const attrs = (opts.attributes as string[]) ?? [];
      if (opts.scope === "base") {
        if (o.breakReadsAfterWrite && log.some((l) => l.op !== "store")) throw new Error("socket hang up");
        const e = entries.find((x) => same(x.dn, base));
        if (!e) throw new NoSuchObjectError("no such object");
        const m = filter.match(/^\(member=(.*)\)$/);
        if (m) return { searchEntries: ([e.member].flat() as string[]).some((d) => d && same(d, unescape(m[1]))) ? [e] : [] };
        const ranged = attrs.find((a) => a.startsWith("member;range="));
        if (ranged && memberPages) {
          const start = Number(ranged.slice("member;range=".length).split("-")[0]);
          let offset = 0;
          for (let i = 0; i < memberPages.length; i++) {
            if (offset === start) {
              const last = i === memberPages.length - 1;
              const key = `member;range=${start}-${last ? "*" : start + memberPages[i].length - 1}`;
              return { searchEntries: [{ dn: e.dn, [key]: memberPages[i] }] };
            }
            offset += memberPages[i].length;
          }
        }
        return { searchEntries: [e] };
      }
      const pg = filter.match(/^\(primaryGroupID=(\d+)\)$/);
      if (pg) return { searchEntries: entries.filter((e) => e.primaryGroupID === pg[1]) };
      const values = [...filter.matchAll(/(?:sAMAccountName|userPrincipalName|cn)=([^)]*)/g)].map((m) => unescape(m[1]).replace(/\$$/, ""));
      const wantUser = filter.startsWith("(&(objectCategory=person)");
      const wantGroup = filter.startsWith("(&(objectClass=group)");
      const hits = entries.filter((e) => {
        const classes = [e.objectClass].flat();
        if (wantUser && !classes.includes("user")) return false;
        if (wantGroup && !classes.includes("group")) return false;
        return values.some((v) => [e.sAMAccountName, e.userPrincipalName, e.cn].some((x) => typeof x === "string" && same(x, v)));
      });
      return { searchEntries: hits };
    },
    async modify(dn, changes) {
      if (o.race) {
        o.race(entries);
        throw new Error("attributeOrValueExists");
      }
      log.push({ op: "modify", dn, arg: changes });
      const e = entries.find((x) => same(x.dn, dn));
      for (const c of [changes].flat()) {
        if (e && c.modification.type === "member") {
          const v = String(c.modification.values[0]);
          const cur = [e.member ?? []].flat() as string[];
          e.member = c.operation === "add" ? [...cur, v] : cur.filter((d) => !same(d, v));
        }
      }
    },
    async add(dn, entry) {
      log.push({ op: "add", dn, arg: entry });
    },
    async modifyDN(dn, newDN) {
      log.push({ op: "modifyDN", dn, arg: newDN });
    },
    async unbind() {},
  };
}

function harness(opts: FakeOpts & { storeFails?: boolean; badConfig?: boolean } = {}) {
  const entries = directory();
  const log: { op: string; dn: string; arg: unknown }[] = [];
  const audits: Record<string, unknown>[] = [];
  const stored: { vault: string; secret: string }[] = [];
  let connects = 0;
  const deps: Deps = {
    config: parseConfig(VALID),
    async connect() {
      connects++;
      return { client: fakeClient(entries, log, opts), dc: "dc01.corp.example.com" };
    },
    async storeSecret(vault, _title, secret) {
      if (opts.storeFails) throw new Error("op item create failed");
      stored.push({ vault, secret });
      log.push({ op: "store", dn: "", arg: vault });
      return `op://${vault}/newitem/password`;
    },
    audit: (r) => audits.push(r),
    generatePassword: () => "Gen3rated!Passw0rd-xyz",
  };
  const run = (...argv: string[]) =>
    main(argv, () => {
      if (opts.badConfig) throw new Error("invalid config:\n  - domain must be a non-empty string");
      return deps;
    });
  return { run, log, audits, stored, connects: () => connects, entries };
}

const changeOf = (arg: unknown) => {
  const c = (Array.isArray(arg) ? arg[0] : arg) as Change;
  return { operation: c.operation, type: c.modification.type, values: c.modification.values };
};

describe("write gate", () => {
  test("writes are dry runs without --apply", async () => {
    const h = harness();
    const r = await h.run("add-member", "app-readers", "jdoe");
    expect(r.code).toBe(EXIT.OK);
    expect((r.out as { mode: string }).mode).toBe("dry-run");
    expect(h.log).toHaveLength(0);
    expect(h.audits).toHaveLength(0);
  });

  test("--apply modifies the group's member attribute and writes an audit line", async () => {
    const h = harness();
    const r = await h.run("add-member", "app-readers", "jdoe", "--apply");
    expect(r.code).toBe(EXIT.OK);
    expect(h.log).toHaveLength(1);
    expect(h.log[0].dn).toBe(GROUP_DN);
    expect(changeOf(h.log[0].arg)).toEqual({ operation: "add", type: "member", values: [JANE_DN] });
    expect(h.audits).toHaveLength(1);
    expect(h.audits[0].result).toBe("applied");
  });

  test("adding an existing member is a no-op", async () => {
    const h = harness();
    (h.entries[0].member as string[]).push(JANE_DN);
    const r = await h.run("add-member", "app-readers", "jdoe", "--apply");
    expect((r.out as { mode: string }).mode).toBe("noop");
    expect(h.log).toHaveLength(0);
  });

  test("protected accounts need --allow-protected", async () => {
    const h = harness();
    const r = await h.run("disable", "radmin", "--apply");
    expect(r.code).toBe(EXIT.REFUSED);
    expect(h.log).toHaveLength(0);
    const ok = await h.run("disable", "radmin", "--apply", "--allow-protected");
    expect(ok.code).toBe(EXIT.OK);
    // delete-old + add-new: AD refuses it if another writer changed the value in between.
    const [del, add] = h.log[0].arg as Change[];
    expect([del.operation, del.modification.values, add.operation, add.modification.values]).toEqual(["delete", ["512"], "add", ["514"]]);
  });

  test("creates outside the OU allowlist are refused before anything is sent", async () => {
    const h = harness();
    const r = await h.run("create-user", "newbie", "--ou", "OU=Admins,DC=corp,DC=example,DC=com", "--given", "New", "--sn", "Bie", "--apply");
    expect(r.code).toBe(EXIT.REFUSED);
    expect(h.log).toHaveLength(0);
  });

  test("create-user escapes the CN and creates the account disabled", async () => {
    const h = harness();
    const r = await h.run("create-user", "doej", "--ou", "OU=Managed,DC=corp,DC=example,DC=com", "--given", "Jane", "--sn", "Doe", "--display", "Doe, Jane");
    const out = r.out as { mode: string; dn: string; changes: { add: Record<string, string> } };
    expect(out.mode).toBe("dry-run");
    expect(out.dn).toBe("CN=Doe\\, Jane,OU=Managed,DC=corp,DC=example,DC=com");
    expect(out.changes.add.userAccountControl).toBe("514");
    expect(out.changes.add.userPrincipalName).toBe("doej@corp.example.com");
    expect(out.changes.add.cn).toBe("Doe, Jane");
  });

  test("set-group-scope refuses global to domainlocal", async () => {
    const h = harness();
    const r = await h.run("set-group-scope", "app-readers", "--scope", "domainlocal", "--apply");
    expect(r.code).toBe(EXIT.REFUSED);
    expect(h.log).toHaveLength(0);
  });

  test("move only targets allowlisted OUs and uses modifyDN", async () => {
    const h = harness();
    expect((await h.run("move", "jdoe", "--to", "OU=Admins,DC=corp,DC=example,DC=com", "--apply")).code).toBe(EXIT.REFUSED);
    const target = "OU=Sub,OU=Managed,DC=corp,DC=example,DC=com";
    h.entries.push({ dn: `CN=Jane Doe,${target}`, objectClass: ["user"] });
    const r = await h.run("move", "jdoe", "--to", target, "--apply");
    expect(r.code).toBe(EXIT.OK);
    expect(h.log[0]).toEqual({ op: "modifyDN", dn: JANE_DN, arg: `CN=Jane Doe,${target}` });
  });
});

describe("reset-password", () => {
  test("stores the secret in the vault before touching AD, and never outputs it", async () => {
    const h = harness();
    const r = await h.run("reset-password", "jdoe", "--must-change", "--apply");
    expect(r.code).toBe(EXIT.OK);
    expect(h.log.map((l) => l.op)).toEqual(["store", "modify"]);
    const changes = h.log[1].arg as Change[];
    expect(changes[0].modification.type).toBe("unicodePwd");
    expect((changes[0].modification.values[0] as Buffer).equals(encodeUnicodePwd("Gen3rated!Passw0rd-xyz"))).toBe(true);
    expect(changes[1].modification.type).toBe("pwdLastSet");
    const printed = JSON.stringify(r.out) + JSON.stringify(h.audits);
    expect(printed).not.toContain("Gen3rated");
    expect(printed).toContain("op://Vault/newitem/password");
  });

  test("a vault failure leaves AD untouched", async () => {
    const h = harness({ storeFails: true });
    const r = await h.run("reset-password", "jdoe", "--apply");
    expect(r.code).toBe(EXIT.FAILED);
    expect(h.log.filter((l) => l.op === "modify")).toHaveLength(0);
  });
});

describe("reads", () => {
  test("group-members follows ranged retrieval to the last page", async () => {
    const pages = [["CN=a,DC=x", "CN=b,DC=x"], ["CN=c,DC=x", "CN=d,DC=x"], ["CN=e,DC=x"]];
    const h = harness({ memberPages: pages });
    const r = await h.run("group-members", "app-readers");
    expect(r.out).toMatchObject({ count: 5, members: pages.flat() });
  });

  test("an ambiguous or missing identity exits NOT_FOUND", async () => {
    const h = harness();
    expect((await h.run("find-user", "nobody")).code).toBe(EXIT.NOT_FOUND);
  });

  test("usage errors never open a connection", async () => {
    const h = harness();
    expect((await h.run("frobnicate")).code).toBe(EXIT.USAGE);
    expect((await h.run("find-user", "--bogus")).code).toBe(EXIT.USAGE);
    expect(h.connects()).toBe(0);
  });
});

describe("review fixes", () => {
  test("a failed read-back still reports applied, and the audit line is written first", async () => {
    const h = harness({ breakReadsAfterWrite: true });
    const r = await h.run("add-member", "app-readers", "jdoe", "--apply");
    expect(r.code).toBe(EXIT.OK);
    expect(r.out).toMatchObject({ mode: "applied", after: { readBackError: expect.stringContaining("socket") } });
    expect(h.audits.map((a) => a.result)).toEqual(["applied"]);
  });

  test("reset-password keeps its vault ref in the audit and the result even when read-back fails", async () => {
    const h = harness({ breakReadsAfterWrite: true });
    const r = await h.run("reset-password", "jdoe", "--apply");
    expect(r.code).toBe(EXIT.OK);
    expect((r.out as { passwordRef: string }).passwordRef).toBe("op://Vault/newitem/password");
    expect(h.audits[0]).toMatchObject({ result: "applied", passwordRef: "op://Vault/newitem/password" });
  });

  test("config errors exit 2, and missing arguments or flags never connect", async () => {
    expect((await harness({ badConfig: true }).run("find-user", "jdoe")).code).toBe(EXIT.USAGE);
    const h = harness();
    expect((await h.run("move", "jdoe")).code).toBe(EXIT.USAGE);
    expect((await h.run("create-user", "x", "--ou", "OU=Managed,DC=corp,DC=example,DC=com")).code).toBe(EXIT.USAGE);
    expect((await h.run("find-user")).code).toBe(EXIT.USAGE);
    expect(h.connects()).toBe(0);
  });

  test("a DN argument must be under baseDn and of the right object class", async () => {
    const h = harness();
    h.entries.push({ dn: "OU=Managed,DC=corp,DC=example,DC=com", objectClass: ["top", "organizationalUnit"] });
    expect((await h.run("find-user", "CN=X,DC=other,DC=com")).code).toBe(EXIT.REFUSED);
    expect((await h.run("find-user", GROUP_DN)).code).toBe(EXIT.REFUSED);
    expect((await h.run("move", "OU=Managed,DC=corp,DC=example,DC=com", "--to", "OU=Sub,OU=Managed,DC=corp,DC=example,DC=com", "--apply")).code).toBe(EXIT.REFUSED);
    expect(h.log).toHaveLength(0);
    expect((await h.run("find-user", "CN=Gone,OU=Managed,DC=corp,DC=example,DC=com")).code).toBe(EXIT.NOT_FOUND);
  });

  test("only a missing object is NOT_FOUND; other LDAP failures surface as failures", async () => {
    const h = harness({ breakReadsAfterWrite: true });
    h.log.push({ op: "modify", dn: "", arg: null });
    expect((await h.run("find-user", JANE_DN)).code).toBe(EXIT.FAILED);
  });

  test("a batch that fails part-way reports the members it already changed", async () => {
    const h = harness();
    const r = await h.run("add-member", "app-readers", "jdoe", "nobody", "--apply");
    expect(r.code).toBe(EXIT.NOT_FOUND);
    const err = r.err as { error: string; detail: { completed: unknown[]; pending: string[] } };
    expect(err.error).toContain("stopped at nobody");
    expect(err.detail.completed).toHaveLength(1);
    expect(err.detail.pending).toEqual(["nobody"]);
  });

  test("a membership change another writer already made counts as applied", async () => {
    const h = harness({ race: (entries) => (entries[0].member as string[]).push(JANE_DN) });
    const r = await h.run("add-member", "app-readers", "jdoe", "--apply");
    expect(r.code).toBe(EXIT.OK);
    expect(r.out).toMatchObject({ mode: "applied", after: { isDirectMember: true } });
  });

  test("group-members includes members whose primary group it is", async () => {
    const h = harness();
    h.entries[0].primaryGroupToken = "1234";
    h.entries[2].primaryGroupID = "1234";
    const r = await h.run("group-members", "app-readers");
    expect(r.out).toMatchObject({ count: 1, viaPrimaryGroup: 1, members: [ADMIN_DN] });
  });

  test("user-groups adds the primary group, found by the user's SID with the RID swapped", async () => {
    const h = harness();
    const domain = "010500000000000515000000aaaaaaaabbbbbbbbcccccccc";
    const rid = (n: number) => {
      const b = Buffer.alloc(4);
      b.writeUInt32LE(n);
      return b.toString("hex");
    };
    h.entries[1].objectSid = Buffer.from(domain + rid(1105), "hex");
    h.entries[1].primaryGroupID = "1234";
    h.entries[0].objectSid = Buffer.from(domain + rid(1234), "hex");
    const r = await h.run("user-groups", "jdoe");
    expect(r.out).toMatchObject({ primaryGroup: GROUP_DN, count: 1, groups: [GROUP_DN] });
  });
});
