#!/usr/bin/env bun
/**
 * rename-skills — mechanically normalize every skill directory under skills/:
 *   1. Lowercase the name (ASCII).
 *   2. Drop a trailing `-skill` suffix.
 *   3. Use `git mv` to preserve history.
 *   4. Handle case-only renames on case-insensitive filesystems via a tmp intermediate.
 *
 * Bun runtime, zero deps. Read --dry-run to preview without acting.
 *
 * Safety: only renames directories that are direct children of skills/. Refuses
 * to act if the target name already exists as a different entry.
 */
import { readdir, stat } from "node:fs/promises";
import { isAbsolute, join, resolve } from "node:path";
import { spawnSync } from "node:child_process";

interface Plan {
  from: string;
  to: string;
  caseOnly: boolean;
}

function parseArgs(argv: string[]): { dryRun: boolean; skillsDir: string } {
  const dryRun = argv.includes("--dry-run");
  const positional = argv.filter((a) => a !== "--dry-run");
  const requested = positional[0] ?? "./skills";
  const skillsDir = isAbsolute(requested) ? requested : resolve(process.cwd(), requested);
  return { dryRun, skillsDir };
}

function computeTarget(name: string): string {
  let next = name.toLowerCase();
  if (next.endsWith("-skill")) {
    next = next.slice(0, -"-skill".length);
  }
  return next;
}

async function safeStat(path: string) {
  try {
    return await stat(path);
  } catch {
    return null;
  }
}

function gitMv(cwd: string, from: string, to: string): { ok: boolean; stderr: string } {
  const result = spawnSync("git", ["mv", from, to], { cwd, encoding: "utf8" });
  if (result.status !== 0) {
    return { ok: false, stderr: result.stderr.trim() || result.stdout.trim() || `exit ${result.status}` };
  }
  return { ok: true, stderr: "" };
}

async function main(): Promise<void> {
  const { dryRun, skillsDir } = parseArgs(process.argv.slice(2));
  const dirStat = await safeStat(skillsDir);
  if (!dirStat || !dirStat.isDirectory()) {
    process.stderr.write(`Invalid skills directory: ${skillsDir}\n`);
    process.exit(2);
  }

  const entries = await readdir(skillsDir, { withFileTypes: true });
  entries.sort((a, b) => a.name.localeCompare(b.name));

  const plans: Plan[] = [];
  const existingNames = new Set(entries.map((e) => e.name));

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    if (entry.name.startsWith(".")) continue;
    const target = computeTarget(entry.name);
    if (target === entry.name) continue;
    if (target !== entry.name && existingNames.has(target) && target.toLowerCase() !== entry.name.toLowerCase()) {
      process.stderr.write(`Conflict: cannot rename ${entry.name} -> ${target} (target exists as a separate entry).\n`);
      process.exit(3);
    }
    plans.push({ from: entry.name, to: target, caseOnly: target.toLowerCase() === entry.name.toLowerCase() });
  }

  if (plans.length === 0) {
    process.stdout.write("No renames needed.\n");
    return;
  }

  process.stdout.write(`Planned renames: ${plans.length}${dryRun ? " (dry run)" : ""}\n`);
  for (const p of plans) {
    process.stdout.write(`  ${p.from}${p.caseOnly ? " [case-only]" : ""} -> ${p.to}\n`);
  }
  if (dryRun) return;

  // Repo root is the parent of skillsDir's parent (skills lives at repo root).
  // For `git mv` we need to run inside the repo and pass paths relative to skillsDir.
  let okCount = 0;
  for (const p of plans) {
    if (p.caseOnly) {
      const tmp = `${p.to}.__rename_tmp__`;
      const step1 = gitMv(skillsDir, p.from, tmp);
      if (!step1.ok) {
        process.stderr.write(`FAIL ${p.from} -> ${tmp}: ${step1.stderr}\n`);
        continue;
      }
      const step2 = gitMv(skillsDir, tmp, p.to);
      if (!step2.ok) {
        process.stderr.write(`FAIL ${tmp} -> ${p.to}: ${step2.stderr} (left as ${tmp}, manual fix needed)\n`);
        continue;
      }
    } else {
      const step = gitMv(skillsDir, p.from, p.to);
      if (!step.ok) {
        process.stderr.write(`FAIL ${p.from} -> ${p.to}: ${step.stderr}\n`);
        continue;
      }
    }
    okCount += 1;
  }
  process.stdout.write(`Renamed: ${okCount}/${plans.length}\n`);
  process.exit(okCount === plans.length ? 0 : 1);
}

void main();
