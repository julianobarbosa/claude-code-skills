#!/usr/bin/env bun
// Create, maintain and lint CHANGELOG.md in Keep a Changelog 1.1.0 format.
//
// Usage:
//   bun Changelog.ts init                          create CHANGELOG.md (refuses to overwrite)
//   bun Changelog.ts add <Type> "<entry>"          Type: Added|Changed|Deprecated|Removed|Fixed|Security
//   bun Changelog.ts release <X.Y.Z> [--date YYYY-MM-DD] [--base main]
//   bun Changelog.ts yank <X.Y.Z>
//   bun Changelog.ts notes <X.Y.Z|Unreleased>      print a section body
//   bun Changelog.ts links [--rewrite]                write missing compare links (--rewrite: all)
//   bun Changelog.ts lint [--strict] [--fix]
// Common: --file <path> (default CHANGELOG.md), --repo-url <url> (default: origin's URL)
//
// Exit codes: 0 ok · 1 lint errors (or warnings with --strict) · 2 usage · 3 refused
// Also imported by ReleaseCut.ts (releaseChangelog) and ReleasePublish.ts (notesFor).

import { existsSync, readFileSync, writeFileSync } from "node:fs";
import {
  Refusal, UsageError, compareSemver, note, out, parseSemver, repoWeb, run, today,
  type RepoWeb,
} from "./Lib.ts";

export const CATEGORIES = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"] as const;
type Category = (typeof CATEGORIES)[number];

export const INIT_TEMPLATE = `# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
`;

interface Line { t: string; n: number }
export interface Section {
  heading: string;
  n: number;
  kind: "unreleased" | "version" | "other";
  version?: string;
  date?: string;
  sep?: string;
  yanked: boolean;
  bracketed: boolean;
  body: Line[];
}
export interface Ref { label: string; url: string; n: number }
export interface Doc { preamble: Line[]; sections: Section[]; refs: Ref[] }

const LINKDEF = /^\[([^\]]+)\]:\s*(\S+)\s*$/;
const UNRELEASED = /^##\s+\[?unreleased\]?(?:\s+.*)?$/i;
// ## [1.2.3] - 2024-01-31 [YANKED]   (brackets, separator, date and marker captured separately)
const VERSION_HEAD = /^##\s+(\[)?(v?\d[^\]\s]*)\]?(?:\s+(\S)\s+(\S+))?(\s+\[YANKED\])?\s*$/;
const ENTRY = /^\s*[-*+]\s+\S/;
const ODD_HYPHENS: Record<string, string> = { "­": "soft hyphen", "‐": "hyphen", "‑": "non-breaking hyphen" };

const isEntry = (t: string) => ENTRY.test(t);
const refKey = (label: string) => label.toLowerCase().replace(/^v/, "");
const cp = (ch: string) => `U+${ch.codePointAt(0)!.toString(16).toUpperCase().padStart(4, "0")}`;

export function isIsoDate(d: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) return false;
  const t = new Date(`${d}T00:00:00Z`);
  return !Number.isNaN(t.getTime()) && t.toISOString().slice(0, 10) === d;
}

// ------------------------------------------------------------------- model

function toSection(t: string, n: number): Section {
  if (UNRELEASED.test(t)) return { heading: t, n, kind: "unreleased", yanked: false, bracketed: /\[unreleased\]/i.test(t), body: [] };
  const m = t.match(VERSION_HEAD);
  if (m) {
    return { heading: t, n, kind: "version", version: m[2].replace(/^v/, ""), sep: m[3], date: m[4], yanked: !!m[5], bracketed: !!m[1], body: [] };
  }
  return { heading: t, n, kind: "other", yanked: false, bracketed: false, body: [] };
}

/** Line-preserving parse: preamble, `## ` sections, and link reference definitions. */
export function parse(text: string): Doc {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  if (lines.at(-1) === "") lines.pop();
  const doc: Doc = { preamble: [], sections: [], refs: [] };
  let cur: Section | null = null;
  for (let i = 0; i < lines.length; i++) {
    const t = lines[i];
    const n = i + 1;
    const ld = t.match(LINKDEF);
    if (ld) {
      doc.refs.push({ label: ld[1], url: ld[2], n });
      continue;
    }
    if (/^##\s/.test(t)) {
      cur = toSection(t, n);
      doc.sections.push(cur);
      continue;
    }
    (cur ? cur.body : doc.preamble).push({ t, n });
  }
  return doc;
}

function trimEnd(ls: Line[]): Line[] {
  const a = [...ls];
  while (a.length && a[a.length - 1].t.trim() === "") a.pop();
  return a;
}
function trimStart(ls: Line[]): Line[] {
  let i = 0;
  while (i < ls.length && ls[i].t.trim() === "") i++;
  return ls.slice(i);
}

/** Version links first, in section order, then every other reference as it was. */
function orderRefs(doc: Doc): Ref[] {
  const keys = doc.sections.map((s) => (s.kind === "unreleased" ? "unreleased" : s.version ?? "")).filter(Boolean);
  const byKey = new Map(doc.refs.map((r) => [refKey(r.label), r] as const));
  const ordered = keys.map((k) => byKey.get(k)).filter((r): r is Ref => !!r);
  return [...ordered, ...doc.refs.filter((r) => !keys.includes(refKey(r.label)))];
}

export function render(doc: Doc): string {
  const lines: string[] = trimEnd(doc.preamble).map((l) => l.t);
  for (const s of doc.sections) {
    if (lines.length) lines.push("");
    lines.push(s.heading);
    lines.push(...trimEnd(s.body).map((l) => l.t));
  }
  if (doc.refs.length) {
    lines.push("");
    lines.push(...orderRefs(doc).map((r) => `[${r.label}]: ${r.url}`));
  }
  return lines.join("\n") + "\n";
}

interface Cat { name: string; n: number; start: number; end: number }
function categories(s: Section): Cat[] {
  const cats: Cat[] = [];
  s.body.forEach((l, i) => {
    const m = l.t.match(/^###\s+(.+?)\s*$/);
    if (!m) return;
    if (cats.length) cats[cats.length - 1].end = i;
    cats.push({ name: m[1], n: l.n, start: i, end: s.body.length });
  });
  return cats;
}
const entries = (s: Section) => s.body.filter((l) => isEntry(l.t));

function dropEmptyCategories(body: Line[]): Line[] {
  const res: Line[] = [];
  const isCat = (t: string) => /^###\s/.test(t);
  let i = 0;
  while (i < body.length) {
    if (!isCat(body[i].t)) {
      res.push(body[i++]);
      continue;
    }
    let j = i + 1;
    while (j < body.length && !isCat(body[j].t)) j++;
    const chunk = body.slice(i, j);
    if (chunk.some((l) => isEntry(l.t))) res.push(...chunk);
    i = j;
  }
  return res;
}

/** How the file spaces things: a blank line after `##` headings, a blank line
 *  between groups. With no evidence either way, the spec example's spacing. */
function layout(doc: Doc): { blankAfterHeading: boolean; blankBetweenGroups: boolean } {
  let after = 0, noAfter = 0, between = 0, noBetween = 0;
  for (const s of doc.sections) {
    const first = s.body[0];
    if (first) {
      if (first.t.trim() === "") after++;
      else if (/^###\s/.test(first.t)) noAfter++;
    }
    let seenGroup = false;
    s.body.forEach((l, i) => {
      if (!/^###\s/.test(l.t)) return;
      if (seenGroup) {
        if (s.body[i - 1].t.trim() === "") between++;
        else noBetween++;
      }
      seenGroup = true;
    });
  }
  return { blankAfterHeading: noAfter <= after, blankBetweenGroups: noBetween <= between };
}

// -------------------------------------------------------------- operations

export function addEntry(text: string, type: string, entry: string): { text: string; added: boolean; category: Category } {
  const cat = CATEGORIES.find((c) => c.toLowerCase() === type.toLowerCase());
  if (!cat) throw new UsageError(`type must be one of ${CATEGORIES.join(", ")}, got '${type}'`);
  const clean = entry.trim().replace(/^[-*+]\s+/, "");
  if (!clean) throw new UsageError("entry text is empty");
  const doc = parse(text);
  let un = doc.sections.find((s) => s.kind === "unreleased");
  if (!un) {
    un = { heading: "## [Unreleased]", n: 0, kind: "unreleased", yanked: false, bracketed: true, body: [] };
    doc.sections.unshift(un);
  }
  const line = `- ${clean}`;
  if (un.body.some((l) => l.t.trim() === line)) return { text, added: false, category: cat };
  const blank = { t: "", n: 0 };
  const style = layout(doc);
  const cats = categories(un);
  const existing = cats.find((c) => c.name.toLowerCase() === cat.toLowerCase());
  if (existing) {
    let at = existing.end;
    while (at > existing.start + 1 && un.body[at - 1].t.trim() === "") at--;
    un.body.splice(at, 0, { t: line, n: 0 });
  } else {
    // New groups go in the conventional order (the spec doesn't enforce one) and
    // follow the file's own spacing, so an edit never reflows someone's layout.
    const order = CATEGORIES.indexOf(cat);
    const next = cats.find((c) => CATEGORIES.indexOf(c.name as Category) > order);
    const block = [{ t: `### ${cat}`, n: 0 }, { t: line, n: 0 }];
    if (next) {
      un.body.splice(next.start, 0, ...block, ...(style.blankBetweenGroups ? [blank] : []));
    } else {
      const b = trimEnd(un.body);
      un.body = b.length
        ? [...b, ...(style.blankBetweenGroups ? [blank] : []), ...block]
        : [...(style.blankAfterHeading ? [blank] : []), ...block];
    }
  }
  return { text: render(doc), added: true, category: cat };
}

export interface ReleaseOpts {
  date: string;
  web?: RepoWeb;
  base?: string;
  tagPrefix?: string;
}

function upsertRef(doc: Doc, label: string, url: string): void {
  const r = doc.refs.find((x) => refKey(x.label) === refKey(label));
  if (r) r.url = url;
  else doc.refs.push({ label, url, n: 0 });
}

/** Compare-link builders. GitHub's format is documented; Azure DevOps' branchCompare
 *  URL (GT = tag, GB = branch) is what its web UI uses but is not documented. */
function linkUrls(w: RepoWeb, base = "main", p = "v") {
  const enc = encodeURIComponent;
  return {
    compare: (a: string, b: string) =>
      w.kind === "github" ? `${w.base}/compare/${p}${a}...${p}${b}` : `${w.base}/branchCompare?baseVersion=GT${enc(p + a)}&targetVersion=GT${enc(p + b)}`,
    toHead: (a: string) =>
      w.kind === "github" ? `${w.base}/compare/${p}${a}...HEAD` : `${w.base}/branchCompare?baseVersion=GT${enc(p + a)}&targetVersion=GB${enc(base)}`,
    tagPage: (a: string) => (w.kind === "github" ? `${w.base}/releases/tag/${p}${a}` : `${w.base}?version=GT${enc(p + a)}`),
  };
}

function setLinks(doc: Doc, version: string, prev: string | undefined, web: RepoWeb, o: ReleaseOpts): void {
  const u = linkUrls(web, o.base, o.tagPrefix);
  upsertRef(doc, "unreleased", u.toHead(version));
  upsertRef(doc, version, prev ? u.compare(prev, version) : u.tagPage(version));
}

/** The repository a changelog already links to, read back from its link references. */
export function webFromRefs(refs: Ref[]): RepoWeb | null {
  for (const r of refs) {
    const g = r.url.match(/^(https:\/\/github\.com\/[^/]+\/[^/]+)\/(?:compare|releases)\//);
    if (g) return { kind: "github", base: g[1] };
    const a = r.url.match(/^(https:\/\/dev\.azure\.com\/[^?#]+?\/_git\/[^/?#]+)(?:\/branchCompare\b|\?)/);
    if (a) return { kind: "azure", base: a[1] };
  }
  return null;
}

/** An explicit or remote-derived URL wins; otherwise the one the file already links to. */
export function resolveWeb(doc: Doc, web?: RepoWeb): RepoWeb | null {
  return web && web.kind !== "unknown" ? web : webFromRefs(doc.refs);
}

/** Write a link reference for [Unreleased] and every version heading. Existing
 *  references stay unless rewrite is set; the oldest version keeps an existing
 *  link even then, because its predecessor may simply not be in the file. */
export function backfillLinks(
  text: string,
  o: { web?: RepoWeb; base?: string; tagPrefix?: string; rewrite?: boolean },
): { text: string; added: number; rewritten: number } {
  const doc = parse(text);
  const web = resolveWeb(doc, o.web);
  if (!web) throw new UsageError("no repository URL: pass --repo-url, or add one link reference by hand");
  const u = linkUrls(web, o.base, o.tagPrefix);
  const versions = doc.sections.filter((s) => s.kind === "version" && s.version && parseSemver(s.version)).map((s) => s.version!);
  const want: { label: string; url: string; keep: boolean }[] = versions.map((v, i) => ({
    label: v,
    url: versions[i + 1] ? u.compare(versions[i + 1], v) : u.tagPage(v),
    keep: !versions[i + 1],
  }));
  if (versions.length && doc.sections.some((s) => s.kind === "unreleased")) {
    want.unshift({ label: "unreleased", url: u.toHead(versions[0]), keep: false });
  }
  let added = 0;
  let rewritten = 0;
  for (const w of want) {
    const r = doc.refs.find((x) => refKey(x.label) === refKey(w.label));
    if (!r) {
      doc.refs.push({ label: w.label, url: w.url, n: 0 });
      added++;
    } else if (o.rewrite && !w.keep && r.url !== w.url) {
      r.url = w.url;
      rewritten++;
    }
  }
  return { text: render(doc), added, rewritten };
}

/** Move [Unreleased] into a new dated version section and rewrite its links. */
export function releaseChangelog(text: string, version: string, o: ReleaseOpts): string {
  const sv = parseSemver(version);
  if (!sv) throw new UsageError(`not SemVer: '${version}'`);
  version = sv.raw;
  if (!isIsoDate(o.date)) throw new UsageError(`date must be YYYY-MM-DD, got '${o.date}'`);
  const doc = parse(text);
  const idx = doc.sections.findIndex((s) => s.kind === "unreleased");
  if (idx < 0) throw new Refusal("no [Unreleased] section to release");
  const un = doc.sections[idx];
  if (!entries(un).length) throw new Refusal("[Unreleased] has no entries; add them before releasing");
  const released = doc.sections.filter((s) => s.kind === "version" && s.version && parseSemver(s.version));
  if (released.some((s) => s.version === version)) throw new Refusal(`${version} is already in the changelog`);
  const prev = released.map((s) => s.version!).sort(compareSemver).at(-1);
  if (prev && compareSemver(version, prev) <= 0) throw new Refusal(`${version} is not greater than ${prev}`);
  const sec: Section = {
    heading: `## [${version}] - ${o.date}`, n: 0, kind: "version", version, date: o.date, sep: "-",
    yanked: false, bracketed: true, body: dropEmptyCategories(un.body),
  };
  un.body = [];
  doc.sections.splice(idx + 1, 0, sec);
  // No usable URL given? Fall back to the repository the file already links to.
  const web = resolveWeb(doc, o.web);
  if (web) setLinks(doc, version, prev, web, o);
  return render(doc);
}

export function yank(text: string, version: string): { text: string; changed: boolean } {
  const key = version.replace(/^v/, "");
  const doc = parse(text);
  const s = doc.sections.find((x) => x.kind === "version" && x.version === key);
  if (!s) throw new Refusal(`${key} is not in the changelog`);
  if (s.yanked) return { text, changed: false };
  s.heading = `${s.heading.replace(/\s+$/, "")} [YANKED]`;
  s.yanked = true;
  return { text: render(doc), changed: true };
}

/** Body of one section (for a tag message, PR text or package description); "" if absent. */
export function notesFor(text: string, version: string): string {
  const doc = parse(text);
  const want = version.toLowerCase() === "unreleased" ? null : version.replace(/^v/, "");
  const s = doc.sections.find((x) => (want ? x.kind === "version" && x.version === want : x.kind === "unreleased"));
  return s ? trimStart(trimEnd(s.body)).map((l) => l.t).join("\n") : "";
}

/** Mechanical fixes only: the separator in version headings and look-alike hyphens in entries. */
export function fixText(text: string): { text: string; fixes: number } {
  let fixes = 0;
  const lines = text.split("\n").map((t) => {
    if (/^##\s/.test(t) && VERSION_HEAD.test(t)) {
      const next = t.replace(/\s+[–—]\s+/, " - ");
      if (next !== t) fixes++;
      return next;
    }
    if (isEntry(t) && /[­‐‑]/.test(t)) {
      fixes++;
      return t.replace(/[‐‑]/g, "-").replace(/­/g, "");
    }
    return t;
  });
  return { text: lines.join("\n"), fixes };
}

// -------------------------------------------------------------------- lint

export interface Finding { level: "error" | "warning"; code: string; line: number; msg: string }

export function lint(text: string): Finding[] {
  const f: Finding[] = [];
  const E = (code: string, line: number, msg: string) => f.push({ level: "error", code, line, msg });
  const W = (code: string, line: number, msg: string) => f.push({ level: "warning", code, line, msg });
  const doc = parse(text);
  const pre = doc.preamble.map((l) => l.t).join("\n");
  if (!/^#\s+\S/m.test(pre)) W("W001", 1, "no '# Changelog' title");
  if (!/semver|semantic versioning/i.test(pre)) W("W002", 1, "the preamble doesn't say whether the project follows Semantic Versioning");

  const secs = doc.sections;
  const unreleased = secs.filter((s) => s.kind === "unreleased");
  if (!unreleased.length) W("W010", 1, "no [Unreleased] section to collect upcoming changes");
  if (unreleased.length > 1) E("E011", unreleased[1].n, "more than one [Unreleased] section");
  if (unreleased.length && secs[0].kind !== "unreleased") E("E012", unreleased[0].n, "[Unreleased] must be the first section");
  for (const u of unreleased) {
    if (!u.bracketed) W("W013", u.n, "write [Unreleased] in brackets so it can link");
    if (/\d{4}-\d{2}-\d{2}/.test(u.heading)) W("W014", u.n, "[Unreleased] should not carry a date");
  }

  const seen = new Set<string>();
  let prev: Section | null = null;
  for (const s of secs) {
    if (s.kind === "other") {
      E("E020", s.n, `unrecognized heading '${s.heading}'; expected '## [X.Y.Z] - YYYY-MM-DD'`);
      continue;
    }
    if (s.kind === "version") {
      const v = s.version!;
      const valid = !!parseSemver(v);
      if (!valid) E("E021", s.n, `'${v}' is not a SemVer version`);
      if (!s.bracketed) W("W022", s.n, `write [${v}] in brackets so the heading can link`);
      if (!s.date) E("E023", s.n, `${v} has no release date`);
      else if (!isIsoDate(s.date)) E("E024", s.n, `${v} date '${s.date}' is not an ISO 8601 date (YYYY-MM-DD)`);
      if (s.sep && s.sep !== "-") W("W025", s.n, `separator '${s.sep}' (${cp(s.sep)}) between version and date; use an ASCII hyphen ' - ' (lint --fix)`);
      if (seen.has(v)) E("E026", s.n, `${v} appears more than once`);
      seen.add(v);
      if (prev && valid && parseSemver(prev.version!)) {
        if (compareSemver(v, prev.version!) >= 0) E("E027", s.n, `${v} is listed below ${prev.version}; the newest version goes first`);
        else if (s.date && prev.date && isIsoDate(s.date) && isIsoDate(prev.date) && s.date > prev.date) {
          W("W028", s.n, `${v} is dated after the newer ${prev.version}`);
        }
      }
      if (valid) prev = s;
      if (!entries(s).length) W("W029", s.n, `${v} lists no changes`);
    }

    const cats = categories(s);
    const names = new Set<string>();
    for (const c of cats) {
      const canon = CATEGORIES.find((x) => x.toLowerCase() === c.name.toLowerCase());
      if (!canon) {
        E("E030", c.n, `unknown change type '### ${c.name}'; use ${CATEGORIES.join(", ")}`);
        continue;
      }
      if (canon !== c.name) W("W031", c.n, `write '### ${canon}'`);
      if (names.has(canon)) E("E032", c.n, `'### ${canon}' appears twice in this section`);
      names.add(canon);
      if (!s.body.slice(c.start + 1, c.end).some((l) => isEntry(l.t))) W("W033", c.n, `'### ${canon}' is empty; remove it`);
    }
    const firstCat = cats.length ? cats[0].start : s.body.length;
    for (const l of s.body.slice(0, firstCat)) if (isEntry(l.t)) W("W034", l.n, "entry is not under a change-type heading");
    for (const l of s.body) {
      if (!isEntry(l.t)) continue;
      const txt = l.t.replace(/^\s*[-*+]\s+/, "");
      if (
        /^[0-9a-f]{7,40}\b/.test(txt) ||
        /^(feat|fix|chore|docs|refactor|perf|test|ci|build|style|revert)(\([^)]*\))?!?:/i.test(txt) ||
        /^merged? (branch|pull request|pr)\b/i.test(txt)
      ) {
        W("W040", l.n, "reads like a commit message; describe the change for users");
      }
      const odd = txt.match(/[­‐‑]/);
      if (odd) W("W041", l.n, `contains ${cp(odd[0])} (${ODD_HYPHENS[odd[0]]}); searches for a plain '-' won't match (lint --fix)`);
    }
  }

  const refKeys = new Set(doc.refs.map((r) => refKey(r.label)));
  const hasVersions = secs.some((s) => s.kind === "version");
  for (const s of secs) {
    if (!s.bracketed) continue;
    const key = s.kind === "unreleased" ? "unreleased" : s.kind === "version" ? s.version! : "";
    if (!key || (key === "unreleased" && !hasVersions)) continue;
    if (!refKeys.has(key)) W("W050", s.n, `[${s.kind === "unreleased" ? "Unreleased" : key}] has no link reference at the bottom`);
  }
  const known = new Set(secs.map((s) => (s.kind === "unreleased" ? "unreleased" : s.version ?? "")));
  for (const r of doc.refs) {
    if (parseSemver(r.label) && !known.has(refKey(r.label))) W("W051", r.n, `link reference [${r.label}] has no matching version`);
  }
  return f.sort((a, b) => a.line - b.line || a.code.localeCompare(b.code));
}

// --------------------------------------------------------------------- CLI

const USAGE = `Usage: bun Changelog.ts <command> [options]
  init                                create CHANGELOG.md (refuses to overwrite)
  add <Type> "<entry>"                Type: ${CATEGORIES.join("|")}
  release <X.Y.Z> [--date YYYY-MM-DD] [--base main]
  yank <X.Y.Z>
  notes <X.Y.Z|Unreleased>
  links [--rewrite]                   write missing compare links (--rewrite: all but the oldest)
  lint [--strict] [--fix]
Common: --file <path> (default CHANGELOG.md), --repo-url <url> (default: origin's URL)`;

if (import.meta.main) {
  await run(() => {
    const argv = process.argv.slice(2);
    let file = "CHANGELOG.md";
    let repoUrl = "";
    let date = "";
    let base = "main";
    let strict = false;
    let fix = false;
    let rewrite = false;
    const pos: string[] = [];
    for (let i = 0; i < argv.length; i++) {
      const a = argv[i];
      switch (a) {
        case "--file": file = argv[++i] ?? ""; break;
        case "--repo-url": repoUrl = argv[++i] ?? ""; break;
        case "--date": date = argv[++i] ?? ""; break;
        case "--base": base = argv[++i] ?? ""; break;
        case "--strict": strict = true; break;
        case "--fix": fix = true; break;
        case "--rewrite": rewrite = true; break;
        case "-h": case "--help": console.log(USAGE); return;
        default:
          if (a.startsWith("--")) throw new UsageError(`unknown option ${a}\n${USAGE}`);
          pos.push(a);
      }
    }
    const [cmd, ...rest] = pos;
    const read = () => {
      if (!existsSync(file)) throw new Refusal(`${file} not found; run 'init' first`);
      return readFileSync(file, "utf8");
    };
    switch (cmd) {
      case "init": {
        if (existsSync(file)) throw new Refusal(`${file} already exists; not overwriting it`);
        writeFileSync(file, INIT_TEMPLATE);
        out("created", file);
        return;
      }
      case "add": {
        if (rest.length < 2) throw new UsageError(USAGE);
        const r = addEntry(read(), rest[0], rest.slice(1).join(" "));
        if (r.added) writeFileSync(file, r.text);
        out("added", r.added);
        out("category", r.category);
        return;
      }
      case "release": {
        if (rest.length !== 1) throw new UsageError(USAGE);
        const text = read();
        const web = resolveWeb(parse(text), repoUrl ? repoWeb(repoUrl) : repoWeb());
        if (!web) note("no URL from --repo-url, origin, or existing links; compare links not written");
        const d = date || today();
        writeFileSync(file, releaseChangelog(text, rest[0], { date: d, web: web ?? undefined, base }));
        out("released", rest[0].replace(/^v/, ""));
        out("date", d);
        out("links", web?.kind ?? "none");
        return;
      }
      case "links": {
        if (rest.length) throw new UsageError(USAGE);
        const r = backfillLinks(read(), { web: repoUrl ? repoWeb(repoUrl) : repoWeb(), base, rewrite });
        if (r.added || r.rewritten) writeFileSync(file, r.text);
        out("links_added", r.added);
        out("links_rewritten", r.rewritten);
        return;
      }
      case "yank": {
        if (rest.length !== 1) throw new UsageError(USAGE);
        const r = yank(read(), rest[0]);
        if (r.changed) writeFileSync(file, r.text);
        out("yanked", rest[0].replace(/^v/, ""));
        out("changed", r.changed);
        return;
      }
      case "notes": {
        if (rest.length !== 1) throw new UsageError(USAGE);
        const n = notesFor(read(), rest[0]);
        if (!n) throw new Refusal(`no entries for ${rest[0]}`);
        console.log(n);
        return;
      }
      case "lint": {
        let text = read();
        if (fix) {
          const r = fixText(text);
          if (r.fixes) writeFileSync(file, r.text);
          text = r.text;
          out("fixed", r.fixes);
        }
        const findings = lint(text);
        for (const x of findings) console.log(`${file}:${x.line}: ${x.level} ${x.code} ${x.msg}`);
        const errors = findings.filter((x) => x.level === "error").length;
        const warnings = findings.length - errors;
        out("errors", errors);
        out("warnings", warnings);
        if (errors || (strict && warnings)) process.exitCode = 1;
        return;
      }
      default:
        throw new UsageError(USAGE);
    }
  });
}
