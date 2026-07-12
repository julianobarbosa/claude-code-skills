#!/usr/bin/env bun
/**
 * lint-skills — validate every skill under skills/ against agent-skills-spec.md.
 * Bun runtime. Zero dependencies. Read-only. Exits 1 if any violation.
 */
import { readdir, readFile, stat } from "node:fs/promises";
import { isAbsolute, join, resolve } from "node:path";

type ViolationType =
  | "MISSING_SKILL_MD"
  | "BAD_DIRECTORY_NAME"
  | "NOT_A_DIRECTORY"
  | "MISSING_FRONTMATTER"
  | "INVALID_FRONTMATTER"
  | "NAME_FIELD_MISMATCH"
  | "EMPTY_DESCRIPTION";

interface ViolationRecord {
  dir: string;
  type: ViolationType;
  issue: string;
  fix: string;
}

interface LintReport {
  totalSkills: number;
  violations: ViolationRecord[];
  summary: { byType: Partial<Record<ViolationType, number>>; passing: number };
}

const VIOLATION_ORDER: readonly ViolationType[] = [
  "MISSING_SKILL_MD",
  "BAD_DIRECTORY_NAME",
  "NOT_A_DIRECTORY",
  "MISSING_FRONTMATTER",
  "INVALID_FRONTMATTER",
  "NAME_FIELD_MISMATCH",
  "EMPTY_DESCRIPTION",
];

const ASCII_HYPHEN_CASE = /^[a-z0-9]+(-[a-z0-9]+)*$/;
const UNICODE_HYPHEN_CASE = /^[\p{Ll}\p{Nd}]+(-[\p{Ll}\p{Nd}]+)*$/u;

function parseArgs(argv: string[]): { json: boolean; skillsDir: string } {
  const json = argv.includes("--json");
  const positional = argv.filter((arg) => arg !== "--json");
  const requested = positional[0] ?? "./skills";
  const skillsDir = isAbsolute(requested) ? requested : resolve(process.cwd(), requested);
  return { json, skillsDir };
}

function stripQuotes(value: string): string {
  if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
    return value.slice(1, -1);
  }
  return value;
}

function indentOf(line: string): number {
  const match = line.match(/^\s*/);
  return match ? match[0].length : 0;
}

function parseFrontmatterFields(lines: string[]): Map<string, string> | null {
  const fields = new Map<string, string>();
  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    const trimmed = line.trim();
    if (trimmed === "" || trimmed.startsWith("#")) {
      continue;
    }
    const match = line.match(/^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$/);
    if (!match) {
      // Non-empty, non-comment, non-key line: ignored per spec.
      continue;
    }
    const [, key, rawValue] = match;
    const value = rawValue.trim();
    if (value.startsWith("|") || value.startsWith(">")) {
      const baseIndent = indentOf(line);
      const buf: string[] = [];
      let j = i + 1;
      while (j < lines.length) {
        const next = lines[j];
        const nextTrim = next.trim();
        if (nextTrim !== "" && indentOf(next) <= baseIndent) {
          break;
        }
        buf.push(nextTrim === "" ? "" : next.slice(baseIndent + 1).trim());
        j += 1;
      }
      fields.set(key, buf.join("\n").trim());
      i = j - 1;
      continue;
    }
    fields.set(key, stripQuotes(value));
  }
  return fields.size === 0 ? null : fields;
}

type FrontmatterResult =
  | { kind: "ok"; fields: Map<string, string> }
  | { kind: "missing" }
  | { kind: "invalid" };

function parseFrontmatter(content: string): FrontmatterResult {
  const lines = content.split(/\r?\n/);
  let start = 0;
  while (start < lines.length && lines[start].trim() === "") {
    start += 1;
  }
  if (start >= lines.length || lines[start].trim() !== "---") {
    return { kind: "missing" };
  }
  let end = start + 1;
  while (end < lines.length && lines[end].trim() !== "---") {
    end += 1;
  }
  if (end >= lines.length) {
    return { kind: "invalid" };
  }
  const fields = parseFrontmatterFields(lines.slice(start + 1, end));
  if (!fields) {
    return { kind: "invalid" };
  }
  return { kind: "ok", fields };
}

class ViolationBag {
  readonly all: ViolationRecord[] = [];
  readonly byType: Record<ViolationType, number> = {
    MISSING_SKILL_MD: 0,
    BAD_DIRECTORY_NAME: 0,
    NOT_A_DIRECTORY: 0,
    MISSING_FRONTMATTER: 0,
    INVALID_FRONTMATTER: 0,
    NAME_FIELD_MISMATCH: 0,
    EMPTY_DESCRIPTION: 0,
  };
  readonly perSkill = new Map<string, number>();

  add(dir: string, type: ViolationType, issue: string, fix: string, countForSkill: boolean): void {
    this.all.push({ dir, type, issue, fix });
    this.byType[type] += 1;
    if (countForSkill) {
      this.perSkill.set(dir, (this.perSkill.get(dir) ?? 0) + 1);
    }
  }

  registerSkill(dir: string): void {
    this.perSkill.set(dir, 0);
  }

  passing(): number {
    let n = 0;
    for (const c of this.perSkill.values()) {
      if (c === 0) {
        n += 1;
      }
    }
    return n;
  }

  nonZeroByType(): Partial<Record<ViolationType, number>> {
    const out: Partial<Record<ViolationType, number>> = {};
    for (const type of VIOLATION_ORDER) {
      if (this.byType[type] > 0) {
        out[type] = this.byType[type];
      }
    }
    return out;
  }
}

async function safeStat(path: string): Promise<Awaited<ReturnType<typeof stat>> | null> {
  try {
    return await stat(path);
  } catch {
    return null;
  }
}

function checkNameField(bag: ViolationBag, dir: string, fields: Map<string, string>): void {
  const name = fields.get("name");
  if (name === undefined) {
    bag.add(dir, "NAME_FIELD_MISMATCH", "Frontmatter is missing required 'name' field.", `Add \`name: ${dir}\` to the frontmatter.`, true);
    return;
  }
  if (!UNICODE_HYPHEN_CASE.test(name)) {
    bag.add(
      dir,
      "NAME_FIELD_MISMATCH",
      `Frontmatter name '${name}' is not valid hyphen-case (lowercase letters/digits with hyphens).`,
      "Rewrite name as hyphen-case lowercase matching the directory.",
      true,
    );
    return;
  }
  if (name !== dir) {
    bag.add(
      dir,
      "NAME_FIELD_MISMATCH",
      `Frontmatter name '${name}' does not match directory name '${dir}'.`,
      `Set name to '${dir}' or rename the directory.`,
      true,
    );
  }
}

function checkDescriptionField(bag: ViolationBag, dir: string, fields: Map<string, string>): void {
  const description = fields.get("description");
  if (description === undefined) {
    bag.add(dir, "EMPTY_DESCRIPTION", "Frontmatter is missing required 'description' field.", "Add a non-empty `description:` to the frontmatter.", true);
    return;
  }
  if (description.trim() === "") {
    bag.add(dir, "EMPTY_DESCRIPTION", "Frontmatter 'description' is empty.", "Provide a non-empty description value.", true);
  }
}

async function lintSkills(skillsDir: string): Promise<LintReport> {
  const entries = await readdir(skillsDir, { withFileTypes: true });
  entries.sort((a, b) => a.name.localeCompare(b.name));

  const bag = new ViolationBag();
  let totalSkills = 0;

  for (const entry of entries) {
    if (entry.name === "agent-skills-spec.md" || entry.name.startsWith(".")) {
      continue;
    }

    if (!entry.isDirectory()) {
      if (entry.name.endsWith(".skill") || entry.name.includes("skill")) {
        bag.add(entry.name, "NOT_A_DIRECTORY", "Top-level entry looks like a skill but is not a directory.", "Convert to a directory or remove from skills/.", false);
      }
      continue;
    }

    const skillDirEntries = await readdir(join(skillsDir, entry.name)).catch(() => [] as string[]);
    if (skillDirEntries.length === 0) {
      // Empty directory — typically an uninitialized git submodule (gitlink) or a
      // placeholder. Not yet a skill; let it pass silently so unrelated infra
      // doesn't gate every skills-markdown commit.
      continue;
    }

    totalSkills += 1;
    bag.registerSkill(entry.name);

    if (!ASCII_HYPHEN_CASE.test(entry.name)) {
      bag.add(entry.name, "BAD_DIRECTORY_NAME", "Directory name must use lowercase ASCII hyphen-case.", "Rename the directory to lowercase ASCII hyphen-case.", true);
    }

    const skillMdPath = join(skillsDir, entry.name, "SKILL.md");
    const skillMdStat = await safeStat(skillMdPath);
    if (!skillMdStat || !skillMdStat.isFile()) {
      bag.add(entry.name, "MISSING_SKILL_MD", "SKILL.md is missing.", "Add a SKILL.md file to this directory.", true);
      continue;
    }

    const content = await readFile(skillMdPath, "utf8");
    const fm = parseFrontmatter(content);

    if (fm.kind === "missing") {
      bag.add(entry.name, "MISSING_FRONTMATTER", "SKILL.md does not start with a YAML frontmatter block.", "Add a leading --- frontmatter block to SKILL.md.", true);
      continue;
    }
    if (fm.kind === "invalid") {
      bag.add(entry.name, "INVALID_FRONTMATTER", "Frontmatter block is not closed with ---.", "Add a closing --- line to the frontmatter.", true);
      continue;
    }

    checkNameField(bag, entry.name, fm.fields);
    checkDescriptionField(bag, entry.name, fm.fields);
  }

  return {
    totalSkills,
    violations: bag.all,
    summary: { byType: bag.nonZeroByType(), passing: bag.passing() },
  };
}

function formatHumanReport(report: LintReport): string {
  const sections: string[] = [];
  for (const type of VIOLATION_ORDER) {
    const items = report.violations.filter((v) => v.type === type);
    if (items.length === 0) {
      continue;
    }
    const lines = [type, ...items.map((v) => `- ${v.dir} | ${v.issue} | ${v.fix}`)];
    sections.push(lines.join("\n"));
  }

  const total = report.violations.length;
  const breakdown = VIOLATION_ORDER.filter((t) => report.summary.byType[t] !== undefined)
    .map((t) => `${t}=${report.summary.byType[t]}`)
    .join(", ");
  const footer =
    total === 0
      ? `Total skills: ${report.totalSkills} | Violations: 0 | Passing: ${report.totalSkills}`
      : `Total skills: ${report.totalSkills} | Violations: ${total} (${breakdown}) | Passing: ${report.summary.passing}`;

  return sections.length === 0 ? footer : `${sections.join("\n\n")}\n\n${footer}`;
}

async function main(): Promise<void> {
  const { json, skillsDir } = parseArgs(process.argv.slice(2));

  const dirStat = await safeStat(skillsDir);
  if (!dirStat || !dirStat.isDirectory()) {
    process.stderr.write(`Invalid skills directory: ${skillsDir}\n`);
    process.exit(2);
  }

  try {
    const report = await lintSkills(skillsDir);
    if (json) {
      process.stdout.write(JSON.stringify(report, null, 2));
    } else {
      process.stdout.write(`${formatHumanReport(report)}\n`);
    }
    process.exit(report.violations.length === 0 ? 0 : 1);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    process.stderr.write(`${message}\n`);
    process.exit(2);
  }
}

void main();
