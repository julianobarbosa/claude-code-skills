#!/usr/bin/env bun
/**
 * mise.toml house-style + safety linter.
 *
 * Usage:  bun lint.ts [path/to/mise.toml] [--strict]   (defaults to ./mise.toml)
 *
 * --strict makes warnings fail the exit code too — use it when gating (pre-commit, CI,
 * workflow validation steps); without it only errors fail.
 *
 * Checks the conventions the mise skill enforces, because a mise.toml is a contract the whole team,
 * CI, and future-you read — surprises in it are expensive:
 *   - pin-versions      runtimes must pin a real version in committed config, not latest/lts
 *   - task-description  every task needs a description (mise tasks is the project's command menu)
 *   - no-inline-secrets a secret-looking literal must be loaded from a redacted file, not inlined
 *   - section-order     tools → env → tasks → settings reads top-down as a reader wants
 *
 * Exit codes: 0 = clean (or warnings/info only without --strict), 1 = at least one error
 * (or any warning with --strict), 2 = could not read/parse.
 *
 * Structured checks parse the TOML via bun's native loader; ordering and secret-literal detection
 * scan the raw text (parsing loses comment/line order and the literal value form).
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

type Level = "error" | "warn" | "info";
interface Finding {
  level: Level;
  rule: string;
  msg: string;
}

const args = process.argv.slice(2);
const strict = args.includes("--strict");
const path = resolve(args.find((a) => a !== "--strict") ?? "mise.toml");

let raw: string;
try {
  raw = readFileSync(path, "utf8");
} catch {
  console.error(`✖ cannot read ${path}`);
  process.exit(2);
}

let data: {
  tools?: Record<string, unknown>;
  tasks?: Record<string, unknown>;
};
try {
  data = (await import(pathToFileURL(path).href)).default ?? {};
} catch (e) {
  console.error(`✖ TOML parse failed: ${(e as Error).message}`);
  process.exit(2);
}

const findings: Finding[] = [];
const add = (level: Level, rule: string, msg: string) =>
  findings.push({ level, rule, msg });

// Language runtimes where `latest`/`lts` in committed config silently breaks reproducibility.
// CLI/lint tooling (prettier, ripgrep…) is intentionally allowed to float, so it's not listed here.
const RUNTIMES = new Set([
  "node", "python", "ruby", "go", "rust", "java", "deno", "bun", "php",
  "elixir", "erlang", "dotnet", "kotlin", "zig", "swift", "crystal", "dart", "gleam",
]);

// 1. pin-versions — runtimes must not use latest/lts in a committed config.
for (const [tool, spec] of Object.entries(data.tools ?? {})) {
  const sep = tool.indexOf(":");
  const [backend, name] = sep === -1 ? ["", tool] : [tool.slice(0, sep), tool.slice(sep + 1)];
  // A backend prefix like npm:/cargo:/go:github.com/… installs a CLI tool, not a runtime;
  // only the version-manager backends can deliver an actual runtime.
  const isRuntime = RUNTIMES.has(name) && ["", "core", "asdf", "vfox"].includes(backend);
  if (!isRuntime) continue;
  const specs = Array.isArray(spec) ? spec : [spec];
  for (const v of specs) {
    const vs = v && typeof v === "object" ? (v as { version?: string }).version : v;
    if (vs === "latest" || vs === "lts") {
      add("warn", "pin-versions",
        `tool '${tool}' uses '${vs}' — pin a real version (e.g. '${tool} = "24"') so clones reproduce`);
    }
  }
}

// 2. task-description — every task should be legible in `mise tasks`.
// Tasks with hide = true never appear there, so they are exempt; string/array
// shorthand tasks can't carry a description and get flagged to expand to a table.
for (const [name, task] of Object.entries(data.tasks ?? {})) {
  const table = task && typeof task === "object" && !Array.isArray(task)
    ? (task as { description?: string; hide?: boolean }) : null;
  if (table?.hide === true) continue;
  if (!table || !("description" in table)) {
    add("warn", "task-description",
      `task '${name}' has no description — add a one-line 'description' so it's meaningful in 'mise tasks'`);
  }
}

// 3. no-inline-secrets — raw scan for secret-looking literals that aren't redacted.
// Multiline-string bodies are skipped (task scripts assign shell vars at runtime, not
// commit time), and keys covered by a top-level `redactions = [...]` glob are exempt.
const SECRETY = /(SECRET|TOKEN|PASSWORD|PASSWD|APIKEY|API_KEY|ACCESS_KEY|PRIVATE_KEY|CLIENT_SECRET)/i;
const globToRe = (g: string) =>
  new RegExp(`^${g.replace(/[.+?^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*")}$`);
const redactionGlobs = [...(raw.match(/^\s*redactions\s*=\s*\[([^\]]*)\]/m)?.[1] ?? "")
  .matchAll(/['"]([^'"]+)['"]/g)].map((g) => globToRe(g[1]));
let multi: string | null = null; // open """ / ''' delimiter while inside a multiline string
raw.split("\n").forEach((line, i) => {
  if (multi) {
    if (line.includes(multi)) multi = null;
    return;
  }
  const open = line.match(/=\s*("""|''')/);
  if (open && !line.slice(line.indexOf(open[1]) + 3).includes(open[1])) {
    multi = open[1];
    return;
  }
  const m =
    line.match(/^\s*([A-Za-z0-9_]+)\s*=\s*(['"])(.*?)\2\s*(?:#.*)?$/) ?? // plain literal, trailing comment ok
    line.match(/^\s*([A-Za-z0-9_]+)\s*=\s*\{.*?\bvalue\s*=\s*(['"])(.+?)\2/); // inline-table { value = '…' }
  if (m && SECRETY.test(m[1]) && m[3].length > 0 && !/redact/i.test(line)
      && !redactionGlobs.some((re) => re.test(m[1]))) {
    add("error", "no-inline-secrets",
      `line ${i + 1}: '${m[1]}' looks like an inlined secret — load it from a git-ignored _.file with redact = true`);
  }
});

// 4. section-order — top-level tables should appear tools → env → tasks → settings.
const RANK = new Map([["tools", 0], ["env", 1], ["tasks", 2], ["settings", 3]]);
let highWater = -1;
let orderOk = true;
for (const line of raw.split("\n")) {
  const m = line.match(/^\s*\[\[?([a-zA-Z0-9_]+)/);
  if (!m) continue;
  const r = RANK.get(m[1]);
  if (r === undefined) continue; // e.g. the [_] scratch table
  if (r < highWater) orderOk = false;
  highWater = Math.max(highWater, r);
}
if (!orderOk) {
  add("info", "section-order",
    "sections are out of house order — arrange as [tools] → [env] → [tasks.*] → [settings]");
}

// Report.
const icon: Record<Level, string> = { error: "✖", warn: "⚠", info: "ℹ" };
if (findings.length === 0) {
  console.log(`✓ ${path} passes mise house-style checks`);
  process.exit(0);
}

const order: Level[] = ["error", "warn", "info"];
findings.sort((a, b) => order.indexOf(a.level) - order.indexOf(b.level));
for (const f of findings) {
  console.log(`${icon[f.level]} [${f.rule}] ${f.msg}`);
}

const errors = findings.filter((f) => f.level === "error").length;
const warns = findings.filter((f) => f.level === "warn").length;
const infos = findings.filter((f) => f.level === "info").length;
console.log(`\n${errors} error(s), ${warns} warning(s), ${infos} info`);
process.exit(errors > 0 || (strict && warns > 0) ? 1 : 0);
