/**
 * AdLib - pure helpers for the ad-onprem-ldap CLI.
 *
 * Everything here is deterministic and network-free so it can be unit tested:
 * escaping, userAccountControl / groupType bit math, unicodePwd encoding,
 * FILETIME conversion, OU allowlist checks, password generation, config parsing.
 */

import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

// =============================================================================
// Escaping
// =============================================================================

/** RFC 4515 filter value escaping. Use for every user-supplied value in a filter. */
export function escapeFilter(value: string): string {
  return value.replace(/[\\*()\0]/g, (c) => "\\" + c.charCodeAt(0).toString(16).padStart(2, "0"));
}

/** RFC 4514 attribute value escaping, for building an RDN such as `CN=<value>`. */
export function escapeDnValue(value: string): string {
  let out = value.replace(/[,+"\\<>;=]/g, (c) => "\\" + c);
  if (out.startsWith(" ") || out.startsWith("#")) out = "\\" + out;
  // Test the raw value: one ending in a backslash and a space still needs its space escaped.
  if (value.endsWith(" ") && value.length > 1) out = out.slice(0, -1) + "\\ ";
  return out;
}

/** Split a DN on unescaped commas, trimming only unescaped edge spaces. */
export function splitDn(dn: string): string[] {
  const parts: string[] = [];
  let cur = "";
  let keep = 0; // length of cur through its last escaped character: never trimmed
  const flush = () => {
    const head = cur.slice(0, keep);
    parts.push((head + cur.slice(keep).trimEnd()).trimStart());
    cur = "";
    keep = 0;
  };
  for (let i = 0; i < dn.length; i++) {
    const c = dn[i];
    if (c === "\\" && i + 1 < dn.length) {
      cur += c + dn[++i];
      keep = cur.length;
    } else if (c === ",") {
      flush();
    } else {
      cur += c;
    }
  }
  flush();
  return parts.filter((p) => p !== "");
}

/** Case- and whitespace-insensitive DN form, for comparisons only (never send it to the server). */
export function normalizeDn(dn: string): string {
  return splitDn(dn)
    .map((rdn) => {
      const eq = rdn.indexOf("=");
      return eq < 0 ? rdn.toLowerCase() : `${rdn.slice(0, eq).trim()}=${rdn.slice(eq + 1).trim()}`.toLowerCase();
    })
    .join(",");
}

/** True when `dn` equals `container` or sits anywhere beneath it. */
export function isDnUnder(dn: string, container: string): boolean {
  const d = normalizeDn(dn);
  const c = normalizeDn(container);
  return d === c || d.endsWith("," + c);
}

export function isAllowedOu(ou: string, allowlist: readonly string[]): boolean {
  return allowlist.some((allowed) => isDnUnder(ou, allowed));
}

/** First RDN of a DN, e.g. `CN=Jane Doe` from `CN=Jane Doe,OU=Users,DC=x`. */
export function rdnOf(dn: string): string {
  return splitDn(dn)[0] ?? dn;
}

export function looksLikeDn(value: string): boolean {
  return /^[A-Za-z][\w-]*=.+,.*[A-Za-z][\w-]*=/.test(value);
}

// =============================================================================
// userAccountControl
// =============================================================================

export const UAC = {
  ACCOUNTDISABLE: 0x2,
  NORMAL_ACCOUNT: 0x200,
  DONT_EXPIRE_PASSWORD: 0x10000,
} as const;

/** Bits of the constructed attribute msDS-User-Account-Control-Computed. */
export const UAC_COMPUTED = {
  LOCKOUT: 0x10,
  PASSWORD_EXPIRED: 0x800000,
} as const;

export function setDisabled(uac: number, disabled: boolean): number {
  return disabled ? uac | UAC.ACCOUNTDISABLE : uac & ~UAC.ACCOUNTDISABLE;
}

export function isDisabled(uac: number): boolean {
  return (uac & UAC.ACCOUNTDISABLE) !== 0;
}

/** New accounts are created as a normal account that is disabled until a password exists. */
export const NEW_USER_UAC = UAC.NORMAL_ACCOUNT | UAC.ACCOUNTDISABLE;

// =============================================================================
// groupType
// =============================================================================

export type GroupScope = "global" | "domainlocal" | "universal";
export type GroupKind = "security" | "distribution";

const SCOPE_BITS: Record<GroupScope, number> = { global: 0x2, domainlocal: 0x4, universal: 0x8 };
const SECURITY_BIT = 0x80000000;

/** AD stores groupType as a signed 32-bit integer (security groups are negative). */
export function encodeGroupType(scope: GroupScope, kind: GroupKind): number {
  return (SCOPE_BITS[scope] | (kind === "security" ? SECURITY_BIT : 0)) | 0;
}

export function decodeGroupType(groupType: number): { scope: GroupScope | "unknown"; kind: GroupKind } {
  const u = groupType >>> 0;
  const scope = (Object.keys(SCOPE_BITS) as GroupScope[]).find((s) => (u & SCOPE_BITS[s]) !== 0) ?? "unknown";
  return { scope, kind: (u & SECURITY_BIT) !== 0 ? "security" : "distribution" };
}

export function parseScope(value: string | undefined): GroupScope | null {
  const v = (value ?? "").toLowerCase().replace(/[-_ ]/g, "");
  return v === "global" || v === "domainlocal" || v === "universal" ? v : null;
}

/**
 * AD only converts scope through Universal: Global and DomainLocal never convert
 * directly into each other. Returns null when the move is legal, else the reason.
 */
export function scopeChangeProblem(from: GroupScope, to: GroupScope): string | null {
  if (from === to) return null;
  if (from === "universal" || to === "universal") return null;
  return `AD cannot convert ${from} directly to ${to}; convert to universal first, then to ${to}`;
}

// =============================================================================
// Passwords and time
// =============================================================================

/** AD's unicodePwd: the password wrapped in double quotes, UTF-16LE. Only writable over LDAPS. */
export function encodeUnicodePwd(password: string): Buffer {
  return Buffer.from(`"${password}"`, "utf16le");
}

const PW_SETS = [
  "ABCDEFGHJKLMNPQRSTUVWXYZ",
  "abcdefghijkmnopqrstuvwxyz",
  "23456789",
  "!@#%^*-_=+.?",
] as const;

function randomIndex(max: number, rand: (n: number) => Uint32Array): number {
  // Rejection sampling keeps the distribution uniform.
  const limit = Math.floor(0x100000000 / max) * max;
  for (;;) {
    const [v] = rand(1);
    if (v < limit) return v % max;
  }
}

const cryptoRand = (n: number) => crypto.getRandomValues(new Uint32Array(n));

/** Random password with at least one character from each class (satisfies AD complexity). */
export function generatePassword(length = 24, rand: (n: number) => Uint32Array = cryptoRand): string {
  if (length < PW_SETS.length) throw new Error(`password length must be >= ${PW_SETS.length}`);
  const all = PW_SETS.join("");
  const chars = PW_SETS.map((set) => set[randomIndex(set.length, rand)]);
  while (chars.length < length) chars.push(all[randomIndex(all.length, rand)]);
  for (let i = chars.length - 1; i > 0; i--) {
    const j = randomIndex(i + 1, rand);
    [chars[i], chars[j]] = [chars[j], chars[i]];
  }
  return chars.join("");
}

const FILETIME_EPOCH_OFFSET_MS = 11644473600000n;
const FILETIME_NEVER = 9223372036854775807n;

/** AD FILETIME (100ns ticks since 1601) to ISO string; null for 0 / never. */
export function filetimeToIso(value: string | number | undefined): string | null {
  if (value === undefined || value === "") return null;
  const ticks = BigInt(value);
  if (ticks <= 0n || ticks === FILETIME_NEVER) return null;
  return new Date(Number(ticks / 10000n - FILETIME_EPOCH_OFFSET_MS)).toISOString();
}

// =============================================================================
// Config
// =============================================================================

export interface AdConfig {
  domain: string;
  baseDn: string;
  dcs: string[];
  port: number;
  bindUpn: string;
  passwordRef: string;
  caBundle: string;
  writeOuAllowlist: string[];
  passwordVault?: string;
}

export function expandHome(p: string): string {
  return p === "~" || p.startsWith("~/") ? join(homedir(), p.slice(1)) : p;
}

export function defaultConfigPath(env: Record<string, string | undefined> = process.env): string {
  return env.AD_ONPREM_CONFIG ?? join(homedir(), ".config", "ad-onprem", "config.json");
}

/** Validate a parsed config object. Throws with every problem listed. */
export function parseConfig(raw: unknown): AdConfig {
  const o = (raw ?? {}) as Record<string, unknown>;
  const problems: string[] = [];
  const str = (k: string) => (typeof o[k] === "string" && (o[k] as string).trim() !== "" ? (o[k] as string) : (problems.push(`${k} must be a non-empty string`), ""));
  const list = (k: string) =>
    Array.isArray(o[k]) && (o[k] as unknown[]).every((v) => typeof v === "string") ? (o[k] as string[]) : (problems.push(`${k} must be an array of strings`), []);

  const cfg: AdConfig = {
    domain: str("domain"),
    baseDn: str("baseDn"),
    dcs: list("dcs"),
    port: typeof o.port === "number" ? o.port : 636,
    bindUpn: str("bindUpn"),
    passwordRef: str("passwordRef"),
    caBundle: expandHome(str("caBundle")),
    writeOuAllowlist: list("writeOuAllowlist"),
    passwordVault: typeof o.passwordVault === "string" ? o.passwordVault : undefined,
  };
  if (cfg.dcs.length === 0 && !problems.some((p) => p.startsWith("dcs"))) problems.push("dcs must list at least one domain controller");
  if (cfg.passwordRef && !cfg.passwordRef.startsWith("op://")) problems.push("passwordRef must be an op:// secret reference");
  if (cfg.port === 389) problems.push("port 389 is plain LDAP; this tool requires LDAPS (636)");
  for (const ou of cfg.writeOuAllowlist) {
    if (cfg.baseDn && !isDnUnder(ou, cfg.baseDn)) problems.push(`writeOuAllowlist entry is outside baseDn: ${ou}`);
  }
  if (problems.length) throw new Error(`invalid config:\n  - ${problems.join("\n  - ")}`);
  return cfg;
}

export function loadConfig(path = defaultConfigPath()): AdConfig {
  let text: string;
  try {
    text = readFileSync(path, "utf8");
  } catch {
    throw new Error(`config not found at ${path} (copy config.example.json there, or set AD_ONPREM_CONFIG)`);
  }
  return parseConfig(JSON.parse(text));
}

// =============================================================================
// Entry helpers
// =============================================================================

export type EntryValue = string | string[] | Buffer | Buffer[] | undefined;

export function asArray(v: EntryValue): string[] {
  if (v === undefined) return [];
  const arr = Array.isArray(v) ? v : [v];
  return arr.map((x) => (Buffer.isBuffer(x) ? x.toString("utf8") : String(x)));
}

export function asString(v: EntryValue): string | undefined {
  return asArray(v)[0];
}

export function asInt(v: EntryValue): number | undefined {
  const s = asString(v);
  return s === undefined || s === "" ? undefined : Number.parseInt(s, 10);
}
