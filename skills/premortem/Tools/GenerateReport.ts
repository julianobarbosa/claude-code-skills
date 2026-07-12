#!/usr/bin/env bun

import { readFileSync, writeFileSync, writeSync } from "node:fs";
import { join, resolve } from "node:path";

type RiskLevel = "low" | "medium" | "high";

interface Failure {
  id: string; title: string; likelihood: RiskLevel; severity: RiskLevel; story: string;
  assumption: string; warningSigns: string[]; mitigation: string; owner?: string;
}

interface Synthesis {
  mostLikely: string; mostDangerous: string; hiddenAssumption: string;
  revisedPlan: string[]; preLaunchChecklist: string[];
}

interface PremortemData {
  subject: string; successDefinition?: string; stakeholders?: string; horizon?: string;
  timestamp?: string; failures: Failure[]; synthesis: Synthesis;
}

interface CliOptions { inputPath: string; html: boolean; outPath?: string; }

const usage = (): string => "Usage: bun GenerateReport.ts <findings.json> [--html] [--out <path>]";
const fail = (message: string): never => { writeSync(2, `${message}\n`); process.exit(1); };
const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === "object" && value !== null && !Array.isArray(value);
const isString = (value: unknown): value is string => typeof value === "string";
const isRiskLevel = (value: unknown): value is RiskLevel => value === "low" || value === "medium" || value === "high";
const isStringArray = (value: unknown): value is string[] => Array.isArray(value) && value.every((item: unknown): item is string => isString(item));
const safeTimestamp = (now: Date): string => now.toISOString().replace(/[:.]/g, "-");
const escapeHtml = (value: string): string => value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
const optionalText = (label: string, value?: string): string => typeof value === "string" && value.trim() !== "" ? `- **${label}:** ${value}` : "";
const optionalMeta = (label: string, value?: string): string => typeof value === "string" && value.trim() !== "" ? `<div><strong>${escapeHtml(label)}:</strong> ${escapeHtml(value)}</div>` : "";

function parseArgs(args: string[]): CliOptions {
  let inputPath: string | undefined;
  let html = false;
  let outPath: string | undefined;

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--html") {
      html = true;
    } else if (arg === "--out") {
      const next = args[index + 1];
      if (next === undefined || next.startsWith("--")) {
        fail(`Missing value for --out.\n${usage()}`);
      } else {
        outPath = next;
        index += 1;
      }
    } else if (arg.startsWith("--")) {
      fail(`Unknown flag: ${arg}\n${usage()}`);
    } else if (inputPath === undefined) {
      inputPath = arg;
    } else {
      fail(`Unexpected extra argument: ${arg}\n${usage()}`);
    }
  }

  if (inputPath === undefined) {
    fail(`Missing required <findings.json> path.\n${usage()}`);
  } else {
    return { inputPath, html, outPath };
  }
}

function expectString(value: unknown, path: string, errors: string[]): value is string {
  if (isString(value)) { return true; } else { errors.push(`${path} must be a string`); return false; }
}

function expectOptionalString(value: unknown, path: string, errors: string[]): value is string | undefined {
  if (value === undefined) { return true; }
  if (isString(value)) { return true; } else { errors.push(`${path} must be a string when provided`); return false; }
}

function expectRiskLevel(value: unknown, path: string, errors: string[]): value is RiskLevel {
  if (isRiskLevel(value)) { return true; } else { errors.push(`${path} must be one of: low, medium, high`); return false; }
}

function expectStringArray(value: unknown, path: string, errors: string[]): value is string[] {
  if (isStringArray(value)) { return true; } else { errors.push(`${path} must be an array of strings`); return false; }
}

function isFailure(value: unknown, path: string, errors: string[]): value is Failure {
  if (isRecord(value)) {
    return [
      expectString(value.id, `${path}.id`, errors),
      expectString(value.title, `${path}.title`, errors),
      expectRiskLevel(value.likelihood, `${path}.likelihood`, errors),
      expectRiskLevel(value.severity, `${path}.severity`, errors),
      expectString(value.story, `${path}.story`, errors),
      expectString(value.assumption, `${path}.assumption`, errors),
      expectStringArray(value.warningSigns, `${path}.warningSigns`, errors),
      expectString(value.mitigation, `${path}.mitigation`, errors),
      expectOptionalString(value.owner, `${path}.owner`, errors),
    ].every(Boolean);
  } else {
    errors.push(`${path} must be an object`);
    return false;
  }
}

function isSynthesis(value: unknown, path: string, errors: string[]): value is Synthesis {
  if (isRecord(value)) {
    return [
      expectString(value.mostLikely, `${path}.mostLikely`, errors),
      expectString(value.mostDangerous, `${path}.mostDangerous`, errors),
      expectString(value.hiddenAssumption, `${path}.hiddenAssumption`, errors),
      expectStringArray(value.revisedPlan, `${path}.revisedPlan`, errors),
      expectStringArray(value.preLaunchChecklist, `${path}.preLaunchChecklist`, errors),
    ].every(Boolean);
  } else {
    errors.push(`${path} must be an object`);
    return false;
  }
}

function isPremortemData(value: unknown, errors: string[]): value is PremortemData {
  if (isRecord(value)) {
    const hasFailures = Array.isArray(value.failures) && value.failures.length > 0;
    if (!hasFailures) { errors.push("failures must be a non-empty array"); }
    const failuresValid = hasFailures
      ? value.failures.map((failure: unknown, index: number) => isFailure(failure, `failures[${index}]`, errors)).every(Boolean)
      : false;
    return [
      expectString(value.subject, "subject", errors),
      expectOptionalString(value.successDefinition, "successDefinition", errors),
      expectOptionalString(value.stakeholders, "stakeholders", errors),
      expectOptionalString(value.horizon, "horizon", errors),
      expectOptionalString(value.timestamp, "timestamp", errors),
      failuresValid,
      isSynthesis(value.synthesis, "synthesis", errors),
    ].every(Boolean);
  } else {
    errors.push("root value must be an object");
    return false;
  }
}

function renderMarkdown(data: PremortemData): string {
  const synthesis = [
    "## Synthesis", "",
    `- **Most Likely Failure:** ${data.synthesis.mostLikely}`,
    `- **Most Dangerous Failure:** ${data.synthesis.mostDangerous}`,
    `- **Hidden Assumption:** ${data.synthesis.hiddenAssumption}`, "",
    "### Revised Plan", "", ...data.synthesis.revisedPlan.map((item: string) => `- ${item}`), "",
    "### Pre-Launch Checklist", "", ...data.synthesis.preLaunchChecklist.map((item: string) => `- ${item}`),
  ];
  const failures = data.failures.flatMap((failure: Failure) => [
    `## ${failure.id}: ${failure.title}`, "",
    `- **Likelihood:** ${failure.likelihood}`,
    `- **Severity:** ${failure.severity}`, "",
    "### Story", "", failure.story, "",
    "### Hidden Assumption", "", failure.assumption, "",
    "### Warning Signs", "", ...failure.warningSigns.map((sign: string) => `- ${sign}`), "",
    "### Mitigation", "", failure.mitigation, "",
    ...(failure.owner && failure.owner.trim() !== "" ? [`**Owner:** ${failure.owner}`, ""] : []),
  ]);
  return [
    `# Premortem Report: ${data.subject}`, "",
    `- **Timestamp:** ${data.timestamp}`,
    optionalText("Success Definition", data.successDefinition),
    optionalText("Stakeholders", data.stakeholders),
    optionalText("Horizon", data.horizon),
    "", ...synthesis, "", ...failures, "---", `Subject: ${data.subject}`, `Timestamp: ${data.timestamp}`,
  ].filter((line: string) => line !== "").join("\n");
}

function renderHtml(data: PremortemData): string {
  const badge = (label: string, level: RiskLevel): string => `<span class="badge ${level}">${escapeHtml(label)}: ${escapeHtml(level)}</span>`;
  const list = (items: string[]): string => `<ul>${items.map((item: string) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
  const cards = data.failures.map((failure: Failure) => `<article class="card"><div class="top"><h2>${escapeHtml(failure.id)}: ${escapeHtml(failure.title)}</h2><div class="badges">${badge("Likelihood", failure.likelihood)}${badge("Severity", failure.severity)}</div></div><section><h3>Story</h3><div class="story">${escapeHtml(failure.story)}</div></section><section><h3>Hidden Assumption</h3><p>${escapeHtml(failure.assumption)}</p></section><section><h3>Warning Signs</h3>${list(failure.warningSigns)}</section><section><h3>Mitigation</h3><p>${escapeHtml(failure.mitigation)}</p>${failure.owner && failure.owner.trim() !== "" ? `<p class="owner"><strong>Owner:</strong> ${escapeHtml(failure.owner)}</p>` : ""}</section></article>`).join("");
  const css = `:root{color-scheme:dark;--bg:#0a0e1a;--panel:#131a2b;--panel2:#1a2338;--text:#edf2ff;--muted:#9fb0d1;--border:#2a3550;--low:#1f9d68;--medium:#d39b2a;--high:#d04f5f}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.wrap{max-width:1100px;margin:0 auto;padding:32px 20px 48px}.hero,.card,footer{background:linear-gradient(180deg,rgba(255,255,255,.03),rgba(255,255,255,.01));border:1px solid var(--border);border-radius:18px}.hero{padding:24px;margin-bottom:24px;box-shadow:0 18px 40px rgba(0,0,0,.28)}.meta,.lists,.grid,section{display:grid;gap:10px}.grid{gap:20px}.card{padding:22px}.top{display:flex;gap:16px;justify-content:space-between;align-items:flex-start;margin-bottom:16px}.badges{display:flex;gap:10px;flex-wrap:wrap}.badge{border-radius:999px;padding:6px 10px;font-size:.9rem;font-weight:700;border:1px solid transparent}.low{background:rgba(31,157,104,.18);color:#7be0b0;border-color:rgba(31,157,104,.34)}.medium{background:rgba(211,155,42,.18);color:#ffd67c;border-color:rgba(211,155,42,.34)}.high{background:rgba(208,79,95,.18);color:#ff9cab;border-color:rgba(208,79,95,.34)}h1,h2,h3,p,ul{margin:0}h1{font-size:2rem;line-height:1.2}h2{font-size:1.35rem;line-height:1.2}h3{font-size:1rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}ul{padding-left:20px}.story{white-space:pre-wrap;background:var(--panel2);border-radius:12px;padding:14px}footer{margin-top:24px;padding:16px 20px;color:var(--muted)}@media (max-width:720px){.top{flex-direction:column}}`;
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Premortem Report - ${escapeHtml(data.subject)}</title><style>${css}</style></head><body><main class="wrap"><section class="hero"><h1>${escapeHtml(data.subject)}</h1><div class="meta"><div><strong>Timestamp:</strong> ${escapeHtml(data.timestamp)}</div>${optionalMeta("Success Definition", data.successDefinition)}${optionalMeta("Stakeholders", data.stakeholders)}${optionalMeta("Horizon", data.horizon)}</div><div class="lists"><section><h3>Most Likely Failure</h3><p>${escapeHtml(data.synthesis.mostLikely)}</p></section><section><h3>Most Dangerous Failure</h3><p>${escapeHtml(data.synthesis.mostDangerous)}</p></section><section><h3>Hidden Assumption</h3><p>${escapeHtml(data.synthesis.hiddenAssumption)}</p></section><section><h3>Revised Plan</h3>${list(data.synthesis.revisedPlan)}</section><section><h3>Pre-Launch Checklist</h3>${list(data.synthesis.preLaunchChecklist)}</section></div></section><section class="grid">${cards}</section><footer>Subject: ${escapeHtml(data.subject)} | Timestamp: ${escapeHtml(data.timestamp)}</footer></main></body></html>`;
}

function loadPremortemData(inputPath: string): PremortemData {
  let rawText = "";
  try { rawText = readFileSync(inputPath, "utf8"); }
  catch (error: unknown) { fail(`Failed to read input file "${inputPath}": ${error instanceof Error ? error.message : "unknown read error"}`); }

  let parsed: unknown;
  try { parsed = JSON.parse(rawText); }
  catch (error: unknown) { fail(`Invalid JSON in "${inputPath}": ${error instanceof Error ? error.message : "unknown parse error"}`); }

  const errors: string[] = [];
  if (isPremortemData(parsed, errors)) { return parsed; } else { fail(`Invalid findings JSON in "${inputPath}": ${errors.join("; ")}`); }
}

function writeTarget(path: string, content: string): void {
  if (path === "/dev/stdout") {
    writeSync(1, content);
  } else if (path === "/dev/stderr") {
    writeSync(2, content);
  } else {
    writeFileSync(path, content, "utf8");
  }
}

function outputResult(content: string, options: CliOptions): void {
  try {
    if (options.html && options.outPath === undefined) {
      const filePath = resolve(join(process.cwd(), `premortem-report-${safeTimestamp(new Date())}.html`));
      writeTarget(filePath, content);
      writeSync(1, `${filePath}\n`);
    } else if (options.outPath !== undefined) {
      writeTarget(options.outPath, content);
    } else {
      writeSync(1, content);
    }
  } catch (error: unknown) {
    const target = options.html && options.outPath === undefined ? "generated HTML report" : options.outPath ?? "stdout";
    fail(`Failed to write output to ${target}: ${error instanceof Error ? error.message : "unknown write error"}`);
  }
}

function main(): void {
  const options = parseArgs(Bun.argv.slice(2));
  const data = loadPremortemData(options.inputPath);
  if (data.timestamp === undefined || data.timestamp.trim() === "") { data.timestamp = new Date().toISOString(); }
  outputResult(options.html ? renderHtml(data) : renderMarkdown(data), options);
}

main();
