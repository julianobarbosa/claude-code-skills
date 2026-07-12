#!/usr/bin/env bun
/**
 * lint.ts — structural validator for Justfiles and `.justfiles/<name>.just` modules.
 *
 * Validates the house conventions documented in ../SKILL.md. Part of the `justfile`
 * skill in the julianobarbosa/claude-code-skills repository.
 *
 * Usage:  bun Tools/lint.ts [directory]   (directory defaults to ".")
 * Exit:   0 if every check passes, 1 if any check fails.
 */

import { readdirSync, readFileSync, existsSync, statSync } from "node:fs";
import { join, basename } from "node:path";

const GREEN = "\x1b[32m";
const RED = "\x1b[31m";
const RESET = "\x1b[0m";

let checks = 0;
let errors = 0;

function pass(label: string): void {
  checks++;
  console.log(`  ${GREEN}PASS${RESET} ${label}`);
}

function fail(label: string, detail = ""): void {
  checks++;
  errors++;
  console.log(`  ${RED}FAIL${RESET} ${label}${detail ? ` — ${detail}` : ""}`);
}

/** Return the recipe name if `line` is a recipe definition, else null. */
function recipeName(line: string): string | null {
  // Recipe defs are unindented, not comments/settings/mods/variables.
  if (line === "" || /^\s/.test(line)) return null;
  if (line.startsWith("#") || line.startsWith("set ") || line.startsWith("mod ")) return null;
  if (/^[A-Za-z_][\w-]*\s*:=/.test(line)) return null; // variable assignment
  // name, optional args/deps, then a single ':' that is not ':='
  const m = line.match(/^([A-Za-z_][\w-]*)(?:[ (][^:]*)?:(?!=)/);
  return m ? m[1] : null;
}

/** Validate one Justfile or module file. */
function checkFile(file: string, isRoot: boolean, hasModules: boolean): void {
  const label = isRoot ? basename(file) : `.justfiles/${basename(file)}`;
  console.log(`\n${label}`);

  const raw = readFileSync(file, "utf8");
  const lines = raw.split("\n");

  // 1. Three-line header.
  const header = [
    "#!/usr/bin/env just --justfile",
    'set shell := ["bash", "-euo", "pipefail", "-c"]',
  ];
  lines[0] === header[0] ? pass("Shebang line") : fail("Shebang line", `got: ${lines[0] ?? "<empty>"}`);
  lines[1] === header[1] ? pass("set shell") : fail("set shell", `got: ${lines[1] ?? "<empty>"}`);
  /^set dotenv-load := (true|false)$/.test(lines[2] ?? "")
    ? pass("set dotenv-load")
    : fail("set dotenv-load", `got: ${lines[2] ?? "<empty>"}`);

  // 2. _default is the first recipe.
  let firstRecipe: string | null = null;
  for (const line of lines) {
    const name = recipeName(line);
    if (name) {
      firstRecipe = name;
      break;
    }
  }
  firstRecipe === "_default"
    ? pass("_default is first recipe")
    : fail("_default is first recipe", `first recipe: ${firstRecipe ?? "<none>"}`);

  // 3. --unsorted present.
  raw.includes("--unsorted") ? pass("--unsorted flag present") : fail("--unsorted flag present");

  // 4. --list-submodules only on root-with-modules.
  if (isRoot && hasModules) {
    raw.includes("--list-submodules")
      ? pass("--list-submodules flag (root with modules)")
      : fail("--list-submodules flag (root with modules)", "_default should use --list-submodules");
  }
  if (!isRoot && raw.includes("--list-submodules")) {
    fail("No --list-submodules in module", "module files must not use --list-submodules");
  }

  // 5. No bare env() — must be env_var_or_default()/env_var().
  const bareEnv = [...raw.matchAll(/\benv\([^)]*\)/g)]
    .map((m) => m[0])
    .filter((s) => !s.startsWith("env_var"));
  bareEnv.length === 0
    ? pass("No bare env() calls")
    : fail("No bare env() calls", `found: ${bareEnv.join(", ")}`);

  // 6. Every recipe has a doc comment directly above it.
  const missingDocs: string[] = [];
  for (let i = 0; i < lines.length; i++) {
    const name = recipeName(lines[i]);
    if (!name) continue;
    const prev = (lines[i - 1] ?? "").trim();
    if (!prev.startsWith("#")) missingDocs.push(name);
  }
  missingDocs.length === 0
    ? pass("Doc comments on all recipes")
    : fail("Doc comments on all recipes", `missing on: ${missingDocs.join(", ")}`);

  if (!isRoot) return;

  // 7. Module imports use explicit quoted paths (root only).
  const bareMods = lines
    .filter((l) => l.startsWith("mod "))
    .filter((l) => !/'[^']+\.just'/.test(l) && !/"[^"]+\.just"/.test(l));
  if (hasModules) {
    bareMods.length === 0
      ? pass("Module imports use explicit paths")
      : fail("Module imports use explicit paths", `bare: ${bareMods.join(", ")}`);
  }

  // 8. Section order: variables → mod imports → recipes (root only).
  let lastVar = -1;
  let firstMod = Infinity;
  let lastMod = -1;
  let firstRec = Infinity;
  lines.forEach((line, idx) => {
    if (/^[A-Za-z_][\w-]*\s*:=/.test(line)) lastVar = idx;
    if (line.startsWith("mod ")) {
      firstMod = Math.min(firstMod, idx);
      lastMod = idx;
    }
    if (recipeName(line)) firstRec = Math.min(firstRec, idx);
  });
  const orderOk =
    !(lastVar > -1 && firstMod < Infinity && lastVar > firstMod) &&
    !(lastVar > -1 && firstRec < Infinity && lastVar > firstRec) &&
    !(lastMod > -1 && firstRec < Infinity && lastMod > firstRec);
  orderOk
    ? pass("Section order (variables → mods → recipes)")
    : fail("Section order (variables → mods → recipes)", "sections are out of order");
}

function main(): void {
  const dir = process.argv[2] ?? ".";

  // Locate the root file by its real on-disk name (reliable even on
  // case-insensitive filesystems, unlike a bare `-f Justfile` test).
  const entries = existsSync(dir) ? readdirSync(dir) : [];
  const hasCapital = entries.includes("Justfile");
  const hasLower = entries.includes("justfile");

  if (!hasCapital && !hasLower) {
    fail("Root file exists", `no Justfile found in ${dir}`);
    console.log(`\n${checks} checks, ${errors} errors`);
    process.exit(1);
  }
  const root = join(dir, hasCapital ? "Justfile" : "justfile");
  hasCapital
    ? pass("Root file named Justfile (capital J)")
    : fail("Root file naming", "found lowercase 'justfile', must be 'Justfile'");

  // Wrong module locations.
  if (existsSync(join(dir, "just")) && statSync(join(dir, "just")).isDirectory()) {
    fail("No modules in just/", "modules belong in .justfiles/");
  }
  for (const e of entries) {
    if (e.endsWith(".just")) fail("No root-level .just files", `found ${e} — modules belong in .justfiles/`);
  }

  // Collect modules.
  const modDir = join(dir, ".justfiles");
  const modules =
    existsSync(modDir) && statSync(modDir).isDirectory()
      ? readdirSync(modDir)
          .filter((f) => f.endsWith(".just"))
          .sort()
          .map((f) => join(modDir, f))
      : [];
  const hasModules = modules.length > 0;

  checkFile(root, true, hasModules);
  for (const m of modules) checkFile(m, false, hasModules);

  console.log(`\n${checks} checks, ${errors} errors`);
  process.exit(errors === 0 ? 0 : 1);
}

main();
