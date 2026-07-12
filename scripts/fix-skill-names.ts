#!/usr/bin/env bun
/**
 * fix-skill-names — set frontmatter `name:` to match the directory name for every
 * skill under skills/. Idempotent. Touches only the `name:` line inside the
 * leading `--- ... ---` block. Bun runtime, zero deps.
 */
import { readdir, readFile, writeFile, stat } from "node:fs/promises";
import { isAbsolute, join, resolve } from "node:path";

interface FixOutcome {
  dir: string;
  status: "ok" | "skip-no-skillmd" | "skip-no-frontmatter" | "skip-unclosed" | "no-change" | "inserted";
  before?: string;
  after?: string;
}

function parseArgs(argv: string[]): { dryRun: boolean; skillsDir: string } {
  const dryRun = argv.includes("--dry-run");
  const positional = argv.filter((a) => a !== "--dry-run");
  const requested = positional[0] ?? "./skills";
  const skillsDir = isAbsolute(requested) ? requested : resolve(process.cwd(), requested);
  return { dryRun, skillsDir };
}

async function safeStat(path: string) {
  try {
    return await stat(path);
  } catch {
    return null;
  }
}

function rewriteFrontmatter(content: string, expectedName: string): { changed: boolean; result: string; before?: string; inserted: boolean } {
  const lines = content.split(/\r?\n/);
  // Walk leading blanks
  let start = 0;
  while (start < lines.length && lines[start].trim() === "") start += 1;
  if (start >= lines.length || lines[start].trim() !== "---") {
    return { changed: false, result: content, inserted: false };
  }
  // Find closing ---
  let end = start + 1;
  while (end < lines.length && lines[end].trim() !== "---") end += 1;
  if (end >= lines.length) {
    return { changed: false, result: content, inserted: false };
  }
  // Look for an existing `name:` line within [start+1, end)
  let nameIdx = -1;
  let beforeValue: string | undefined;
  for (let i = start + 1; i < end; i += 1) {
    const m = lines[i].match(/^(\s*)name\s*:\s*(.*)$/);
    if (m) {
      nameIdx = i;
      beforeValue = m[2].trim();
      break;
    }
  }
  const targetLine = `name: ${expectedName}`;
  if (nameIdx !== -1) {
    if (beforeValue === expectedName) {
      return { changed: false, result: content, before: beforeValue, inserted: false };
    }
    const newLines = [...lines];
    newLines[nameIdx] = targetLine;
    return { changed: true, result: newLines.join("\n"), before: beforeValue, inserted: false };
  }
  // No name field — insert at start+1
  const newLines = [...lines];
  newLines.splice(start + 1, 0, targetLine);
  return { changed: true, result: newLines.join("\n"), inserted: true };
}

async function processSkill(skillsDir: string, dir: string, dryRun: boolean): Promise<FixOutcome> {
  const skillMdPath = join(skillsDir, dir, "SKILL.md");
  const st = await safeStat(skillMdPath);
  if (!st || !st.isFile()) {
    return { dir, status: "skip-no-skillmd" };
  }
  const content = await readFile(skillMdPath, "utf8");
  const { changed, result, before, inserted } = rewriteFrontmatter(content, dir);
  if (!changed) {
    // Determine which non-change state we're in
    const lines = content.split(/\r?\n/);
    let s = 0;
    while (s < lines.length && lines[s].trim() === "") s += 1;
    if (s >= lines.length || lines[s].trim() !== "---") {
      return { dir, status: "skip-no-frontmatter" };
    }
    let e = s + 1;
    while (e < lines.length && lines[e].trim() !== "---") e += 1;
    if (e >= lines.length) {
      return { dir, status: "skip-unclosed" };
    }
    return { dir, status: "no-change", before };
  }
  if (!dryRun) {
    await writeFile(skillMdPath, result, "utf8");
  }
  return { dir, status: inserted ? "inserted" : "ok", before, after: dir };
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

  const outcomes: FixOutcome[] = [];
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    if (entry.name === "agent-skills-spec.md" || entry.name.startsWith(".")) continue;
    outcomes.push(await processSkill(skillsDir, entry.name, dryRun));
  }

  const fixed = outcomes.filter((o) => o.status === "ok");
  const inserted = outcomes.filter((o) => o.status === "inserted");
  const noChange = outcomes.filter((o) => o.status === "no-change");
  const skipped = outcomes.filter((o) => o.status.startsWith("skip-"));

  if (fixed.length > 0) {
    process.stdout.write(`UPDATED name: (${fixed.length})\n`);
    for (const o of fixed) {
      process.stdout.write(`  ${o.dir}: '${o.before ?? "?"}' -> '${o.after}'\n`);
    }
  }
  if (inserted.length > 0) {
    process.stdout.write(`INSERTED name: (${inserted.length})\n`);
    for (const o of inserted) process.stdout.write(`  ${o.dir}\n`);
  }
  if (skipped.length > 0) {
    process.stdout.write(`SKIPPED (${skipped.length})\n`);
    for (const o of skipped) process.stdout.write(`  ${o.dir} [${o.status}]\n`);
  }
  const summary = `Total dirs: ${outcomes.length} | Updated: ${fixed.length} | Inserted: ${inserted.length} | No change: ${noChange.length} | Skipped: ${skipped.length}${dryRun ? " | DRY RUN (no writes)" : ""}\n`;
  process.stdout.write(summary);
}

void main();
