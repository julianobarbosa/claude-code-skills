#!/usr/bin/env bun
/**
 * check-no-identity — block personal and employer identifiers from reaching this
 * public repo. Bun runtime. Zero dependencies. Read-only. Exits 1 on any hit.
 *
 * Scans the paths given on argv (pre-commit passes staged files). With no args it
 * scans every tracked file, which is what CI and `--all-files` do.
 *
 * Why this exists: a skill-creator eval tree was committed in 78c6256 carrying real
 * transcripts — corporate emails, employer name, the live Azure DevOps org, and
 * local home paths. Secret scanners pass that content clean, because none of it is
 * a secret. This catches the identity class instead.
 */
import { readFile } from "node:fs/promises";

interface Rule {
  id: string;
  pattern: RegExp;
  why: string;
}

/** Placeholder identities that are meant to be in documentation. */
const ALLOWED = [
  /@(example|test|invalid|localhost)\.(com|org|net)\b/i,
  /@(company|domain|email|acme|yourdomain|your-org)\.(com|br)\b/i,
  /\byour[-.]?(email|org|name|user)\b/i,
  /@x\.com\b/i,
  // conventional placeholder usernames in documentation paths
  /\/(?:home|Users)\/(?:opuser|bob|alice|ubuntu|node|app|runner|vscode|me|you)\//i,
];

/**
 * Employer and internal-project names are deliberately NOT hardcoded here: writing them
 * into a public repo would publish the very list we are trying to keep out of it. They
 * live in an untracked `.identity-denylist` (one term per line, `#` comments allowed).
 * See `.identity-denylist.example`. No file, no EMPLOYER rule — the structural rules
 * below still run, and they are what caught the original leak anyway.
 */
async function employerRule(): Promise<Rule | null> {
  const file = Bun.file(".identity-denylist");
  if (!(await file.exists())) return null;
  const terms = (await file.text())
    .split("\n")
    .map((l) => l.replace(/#.*$/, "").trim())
    .filter(Boolean)
    .map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  if (terms.length === 0) return null;
  return {
    id: "EMPLOYER",
    pattern: new RegExp(`\\b(${terms.join("|")})\\b`, "i"),
    why: "employer / internal project identifier (.identity-denylist)",
  };
}

const RULES: Rule[] = [
  {
    id: "CORP_EMAIL",
    pattern: /[A-Za-z0-9._%+-]+@(?!example|test)[A-Za-z0-9.-]+\.(com\.br|ind\.br)\b/i,
    why: "corporate email address",
  },
  {
    id: "PERSONAL_EMAIL",
    pattern: /[A-Za-z0-9._%+-]+@(gmail|outlook|hotmail|proton(mail)?|icloud|yahoo)\.[a-z.]+/i,
    why: "personal email address",
  },
  {
    id: "HOME_PATH",
    pattern: /(?:^|[\s"'`=(])\/(?:home|Users)\/(?!<|\$|user\b|USER\b)[a-z][a-z0-9._-]*\//i,
    why: "absolute home path (leaks the local username)",
  },
  {
    id: "ADO_ORG",
    pattern: /dev\.azure\.com\/(?!org\b|ORG\b|my-?org\b|your-?org\b|acme\b|<)[A-Za-z0-9._-]+/,
    why: "real Azure DevOps organization name",
  },
];

interface Finding {
  file: string;
  line: number;
  rule: Rule;
  text: string;
}

function isAllowed(text: string): boolean {
  return ALLOWED.some((allow) => allow.test(text));
}

async function scanFile(file: string): Promise<Finding[]> {
  let content: string;
  try {
    content = await readFile(file, "utf8");
  } catch {
    return []; // deleted, binary, or unreadable — nothing to check
  }
  if (content.includes("\u0000")) return [];

  const findings: Finding[] = [];
  const lines = content.split("\n");
  for (const [index, line] of lines.entries()) {
    if (line.includes("check-no-identity-allow")) continue;
    if (isAllowed(line)) continue;
    for (const rule of RULES) {
      if (rule.pattern.test(line)) {
        findings.push({ file, line: index + 1, rule, text: line.trim().slice(0, 160) });
      }
    }
  }
  return findings;
}

async function trackedFiles(): Promise<string[]> {
  const proc = Bun.spawn(["git", "ls-files"], { stdout: "pipe" });
  const out = await new Response(proc.stdout).text();
  return out.split("\n").filter(Boolean);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2).filter((a) => a !== "--all-files");
  const candidates = args.length > 0 ? args : await trackedFiles();
  // the guard's own source states the patterns it hunts for; scanning it is noise
  const files = candidates.filter((f) => !f.endsWith("scripts/check-no-identity.ts"));

  const employer = await employerRule();
  if (employer) RULES.unshift(employer);

  const findings = (await Promise.all(files.map(scanFile))).flat();

  if (findings.length === 0) {
    process.stdout.write(`check-no-identity: ${files.length} file(s) clean\n`);
    process.exit(0);
  }

  process.stderr.write(`check-no-identity: ${findings.length} identity leak(s) blocked\n\n`);
  for (const f of findings) {
    process.stderr.write(`  ${f.file}:${f.line}  [${f.rule.id}] ${f.rule.why}\n`);
    process.stderr.write(`    ${f.text}\n`);
  }
  process.stderr.write(
    "\nThis repo is PUBLIC. Replace with a placeholder, or append the marker\n" +
      "'check-no-identity-allow' to the line if the match is genuinely a false positive.\n",
  );
  process.exit(1);
}

void main();
