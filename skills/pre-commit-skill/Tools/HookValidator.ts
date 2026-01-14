#!/usr/bin/env bun
/**
 * HookValidator - Validate pre-commit hook configurations
 *
 * Usage:
 *   bun run HookValidator.ts [options]
 *
 * Validates:
 *   - YAML syntax
 *   - Required fields
 *   - Version formats
 *   - Hook availability
 *   - Configuration consistency
 */

import { existsSync, readFileSync } from "fs";
import { parse as parseYaml } from "yaml";
import { $ } from "bun";

interface Hook {
  id: string;
  name?: string;
  alias?: string;
  entry?: string;
  language?: string;
  language_version?: string;
  files?: string;
  exclude?: string;
  types?: string[];
  types_or?: string[];
  exclude_types?: string[];
  args?: string[];
  stages?: string[];
  additional_dependencies?: string[];
  always_run?: boolean;
  pass_filenames?: boolean;
  require_serial?: boolean;
  verbose?: boolean;
  log_file?: string;
}

interface Repo {
  repo: string;
  rev: string;
  hooks: Hook[];
}

interface PreCommitConfig {
  repos: Repo[];
  default_install_hook_types?: string[];
  default_language_version?: Record<string, string>;
  default_stages?: string[];
  files?: string;
  exclude?: string;
  fail_fast?: boolean;
  minimum_pre_commit_version?: string;
}

interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  info: string[];
}

const CONFIG_FILE = ".pre-commit-config.yaml";

const VALID_STAGES = [
  "pre-commit",
  "pre-merge-commit",
  "pre-push",
  "commit-msg",
  "post-checkout",
  "post-commit",
  "post-merge",
  "post-rewrite",
  "prepare-commit-msg",
  "pre-rebase",
];

const VALID_LANGUAGES = [
  "python",
  "node",
  "ruby",
  "rust",
  "golang",
  "swift",
  "docker",
  "docker_image",
  "dotnet",
  "lua",
  "perl",
  "r",
  "script",
  "system",
  "fail",
  "pygrep",
];

const COMMON_FILE_TYPES = [
  "text",
  "binary",
  "executable",
  "python",
  "javascript",
  "jsx",
  "ts",
  "tsx",
  "json",
  "yaml",
  "toml",
  "xml",
  "html",
  "css",
  "scss",
  "markdown",
  "shell",
  "bash",
  "zsh",
  "go",
  "rust",
  "java",
  "c",
  "cpp",
  "dockerfile",
  "terraform",
  "hcl",
];

function loadConfig(filePath: string): PreCommitConfig | null {
  if (!existsSync(filePath)) {
    console.error(`❌ ${filePath} not found`);
    return null;
  }

  try {
    const content = readFileSync(filePath, "utf-8");
    return parseYaml(content) as PreCommitConfig;
  } catch (error) {
    console.error(`❌ Failed to parse ${filePath}:`, error);
    return null;
  }
}

function validateRegex(pattern: string, fieldName: string): string | null {
  try {
    new RegExp(pattern);
    return null;
  } catch {
    return `Invalid regex in ${fieldName}: ${pattern}`;
  }
}

function validateVersion(rev: string, repoUrl: string): string | null {
  if (repoUrl === "local" || repoUrl === "meta") {
    return null;
  }

  // Valid formats: v1.0.0, v1.0, 1.0.0, commit SHA (7-40 hex chars)
  const versionPattern = /^v?\d+\.\d+(\.\d+)?(-[\w.]+)?$/;
  const shaPattern = /^[a-f0-9]{7,40}$/;

  if (versionPattern.test(rev) || shaPattern.test(rev)) {
    return null;
  }

  return `Suspicious 'rev' format '${rev}' - use version tags (v1.0.0) or commit SHAs`;
}

function validateHook(hook: Hook, repoUrl: string, repoIndex: number, hookIndex: number): ValidationResult {
  const result: ValidationResult = {
    valid: true,
    errors: [],
    warnings: [],
    info: [],
  };

  const prefix = `Repo ${repoIndex + 1}, Hook ${hookIndex + 1}`;

  // Required: id
  if (!hook.id) {
    result.errors.push(`${prefix}: Missing required 'id' field`);
    result.valid = false;
    return result;
  }

  const hookPrefix = `${prefix} (${hook.id})`;

  // Local hooks require additional fields
  if (repoUrl === "local") {
    if (!hook.name) {
      result.warnings.push(`${hookPrefix}: Local hooks should have a 'name'`);
    }
    if (!hook.entry) {
      result.errors.push(`${hookPrefix}: Local hooks require 'entry'`);
      result.valid = false;
    }
    if (!hook.language) {
      result.errors.push(`${hookPrefix}: Local hooks require 'language'`);
      result.valid = false;
    }
  }

  // Validate language
  if (hook.language && !VALID_LANGUAGES.includes(hook.language.toLowerCase())) {
    result.warnings.push(
      `${hookPrefix}: Unknown language '${hook.language}' - valid: ${VALID_LANGUAGES.join(", ")}`
    );
  }

  // Validate stages
  if (hook.stages) {
    for (const stage of hook.stages) {
      if (!VALID_STAGES.includes(stage)) {
        result.errors.push(
          `${hookPrefix}: Invalid stage '${stage}' - valid: ${VALID_STAGES.join(", ")}`
        );
        result.valid = false;
      }
    }
  }

  // Validate file types
  const allTypes = [...(hook.types || []), ...(hook.types_or || []), ...(hook.exclude_types || [])];
  for (const type of allTypes) {
    if (!COMMON_FILE_TYPES.includes(type)) {
      result.info.push(`${hookPrefix}: Uncommon file type '${type}'`);
    }
  }

  // Validate regex patterns
  if (hook.files) {
    const regexError = validateRegex(hook.files, "files");
    if (regexError) {
      result.errors.push(`${hookPrefix}: ${regexError}`);
      result.valid = false;
    }
  }

  if (hook.exclude) {
    const regexError = validateRegex(hook.exclude, "exclude");
    if (regexError) {
      result.errors.push(`${hookPrefix}: ${regexError}`);
      result.valid = false;
    }
  }

  // Warn about conflicting options
  if (hook.types && hook.types_or) {
    result.warnings.push(
      `${hookPrefix}: Using both 'types' (AND) and 'types_or' (OR) - this may cause confusion`
    );
  }

  if (hook.always_run && hook.files) {
    result.warnings.push(
      `${hookPrefix}: 'always_run: true' with 'files' pattern may be redundant`
    );
  }

  return result;
}

function validateRepo(repo: Repo, index: number): ValidationResult {
  const result: ValidationResult = {
    valid: true,
    errors: [],
    warnings: [],
    info: [],
  };

  const prefix = `Repo ${index + 1}`;

  // Validate repo URL
  if (!repo.repo) {
    result.errors.push(`${prefix}: Missing 'repo' field`);
    result.valid = false;
    return result;
  }

  const repoPrefix = `${prefix} (${repo.repo})`;

  // Validate rev
  if (repo.repo !== "local" && repo.repo !== "meta") {
    if (!repo.rev) {
      result.errors.push(`${repoPrefix}: Missing 'rev' field`);
      result.valid = false;
    } else {
      const versionWarning = validateVersion(repo.rev, repo.repo);
      if (versionWarning) {
        result.warnings.push(`${repoPrefix}: ${versionWarning}`);
      }
    }
  }

  // Validate hooks
  if (!repo.hooks || repo.hooks.length === 0) {
    result.errors.push(`${repoPrefix}: No hooks defined`);
    result.valid = false;
  } else {
    for (let i = 0; i < repo.hooks.length; i++) {
      const hookResult = validateHook(repo.hooks[i], repo.repo, index, i);
      result.errors.push(...hookResult.errors);
      result.warnings.push(...hookResult.warnings);
      result.info.push(...hookResult.info);
      if (!hookResult.valid) {
        result.valid = false;
      }
    }

    // Check for duplicate hook IDs
    const hookIds = repo.hooks.map((h) => h.id);
    const duplicates = hookIds.filter((id, idx) => hookIds.indexOf(id) !== idx);
    if (duplicates.length > 0) {
      result.warnings.push(
        `${repoPrefix}: Duplicate hook IDs: ${[...new Set(duplicates)].join(", ")}`
      );
    }
  }

  return result;
}

function validateConfig(config: PreCommitConfig): ValidationResult {
  const result: ValidationResult = {
    valid: true,
    errors: [],
    warnings: [],
    info: [],
  };

  // Validate top-level structure
  if (!config.repos || !Array.isArray(config.repos)) {
    result.errors.push("Missing or invalid 'repos' field");
    result.valid = false;
    return result;
  }

  if (config.repos.length === 0) {
    result.errors.push("No repositories defined");
    result.valid = false;
    return result;
  }

  // Validate default_stages
  if (config.default_stages) {
    for (const stage of config.default_stages) {
      if (!VALID_STAGES.includes(stage)) {
        result.errors.push(`Invalid default_stage '${stage}'`);
        result.valid = false;
      }
    }
  }

  // Validate global patterns
  if (config.files) {
    const regexError = validateRegex(config.files, "files");
    if (regexError) {
      result.errors.push(regexError);
      result.valid = false;
    }
  }

  if (config.exclude) {
    const regexError = validateRegex(config.exclude, "exclude");
    if (regexError) {
      result.errors.push(regexError);
      result.valid = false;
    }
  }

  // Validate each repository
  for (let i = 0; i < config.repos.length; i++) {
    const repoResult = validateRepo(config.repos[i], i);
    result.errors.push(...repoResult.errors);
    result.warnings.push(...repoResult.warnings);
    result.info.push(...repoResult.info);
    if (!repoResult.valid) {
      result.valid = false;
    }
  }

  // Check for duplicate repositories
  const repoUrls = config.repos.map((r) => r.repo);
  const duplicateRepos = repoUrls.filter((url, idx) => repoUrls.indexOf(url) !== idx);
  if (duplicateRepos.length > 0) {
    result.warnings.push(
      `Duplicate repositories: ${[...new Set(duplicateRepos)].join(", ")}`
    );
  }

  return result;
}

async function checkHookAvailability(config: PreCommitConfig): Promise<string[]> {
  const warnings: string[] = [];

  // Try to run pre-commit to check hook availability
  try {
    await $`pre-commit --version`.quiet();
  } catch {
    return ["pre-commit not installed - skipping hook availability check"];
  }

  for (const repo of config.repos) {
    if (repo.repo === "local" || repo.repo === "meta") {
      continue;
    }

    for (const hook of repo.hooks) {
      try {
        // Use try-repo to check if hook exists (dry-run)
        await $`pre-commit try-repo ${repo.repo} --rev ${repo.rev} ${hook.id} --verbose 2>&1`.quiet();
      } catch {
        // Hook might not exist or repo might not be accessible
        warnings.push(`Hook '${hook.id}' from '${repo.repo}' may not be available`);
      }
    }
  }

  return warnings;
}

function printResult(result: ValidationResult, verbose: boolean): void {
  const totalIssues = result.errors.length + result.warnings.length;

  if (result.errors.length > 0) {
    console.log("\n❌ Errors:");
    result.errors.forEach((e) => console.log(`   ${e}`));
  }

  if (result.warnings.length > 0) {
    console.log("\n⚠️  Warnings:");
    result.warnings.forEach((w) => console.log(`   ${w}`));
  }

  if (verbose && result.info.length > 0) {
    console.log("\nℹ️  Info:");
    result.info.forEach((i) => console.log(`   ${i}`));
  }

  console.log("\n" + "─".repeat(50));

  if (result.valid && result.warnings.length === 0) {
    console.log("✅ Configuration is valid!");
  } else if (result.valid) {
    console.log(`✅ Configuration is valid with ${result.warnings.length} warning(s)`);
  } else {
    console.log(`❌ Configuration has ${result.errors.length} error(s)`);
  }
}

function showHelp(): void {
  console.log(`
HookValidator - Validate pre-commit hook configurations

Usage:
  bun run HookValidator.ts [options]

Options:
  --file, -f <path>    Config file path (default: .pre-commit-config.yaml)
  --verbose, -v        Show info messages
  --check-availability Check if hooks are available (slow)
  --json               Output as JSON
  --help, -h           Show this help

Validates:
  - YAML syntax
  - Required fields (repo, rev, id)
  - Version/rev format
  - Stage names
  - Language types
  - Regex patterns
  - Duplicate detection

Examples:
  bun run HookValidator.ts
  bun run HookValidator.ts --verbose
  bun run HookValidator.ts --file custom-config.yaml
  bun run HookValidator.ts --check-availability
`);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);

  if (args.includes("--help") || args.includes("-h")) {
    showHelp();
    process.exit(0);
  }

  // Parse options
  const fileIndex = args.findIndex((a) => a === "--file" || a === "-f");
  const configFile = fileIndex > -1 ? args[fileIndex + 1] : CONFIG_FILE;
  const verbose = args.includes("--verbose") || args.includes("-v");
  const checkAvailability = args.includes("--check-availability");
  const jsonOutput = args.includes("--json");

  console.log(`🔍 Validating ${configFile}...\n`);

  // Load configuration
  const config = loadConfig(configFile);
  if (!config) {
    process.exit(1);
  }

  // Validate configuration
  const result = validateConfig(config);

  // Check hook availability if requested
  if (checkAvailability) {
    console.log("Checking hook availability (this may take a while)...");
    const availabilityWarnings = await checkHookAvailability(config);
    result.warnings.push(...availabilityWarnings);
  }

  // Output results
  if (jsonOutput) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    // Summary
    console.log("📊 Summary:");
    console.log(`   Repositories: ${config.repos.length}`);
    const hookCount = config.repos.reduce((acc, r) => acc + r.hooks.length, 0);
    console.log(`   Total Hooks: ${hookCount}`);

    printResult(result, verbose);
  }

  process.exit(result.valid ? 0 : 1);
}

main().catch(console.error);
