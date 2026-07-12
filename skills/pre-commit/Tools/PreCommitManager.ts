#!/usr/bin/env bun
/**
 * PreCommitManager - CLI tool for managing pre-commit configurations
 *
 * Usage:
 *   bun run PreCommitManager.ts <command> [options]
 *
 * Commands:
 *   status     - Show pre-commit installation status
 *   install    - Install pre-commit hooks
 *   run        - Run hooks on files
 *   update     - Update hooks to latest versions
 *   clean      - Clean cached environments
 *   validate   - Validate configuration file
 */

import { $ } from "bun";
import { existsSync, readFileSync } from "fs";
import { parse as parseYaml } from "yaml";

interface Hook {
  id: string;
  name?: string;
  args?: string[];
  files?: string;
  exclude?: string;
  stages?: string[];
  additional_dependencies?: string[];
}

interface Repo {
  repo: string;
  rev: string;
  hooks: Hook[];
}

interface PreCommitConfig {
  repos: Repo[];
  default_stages?: string[];
  fail_fast?: boolean;
  files?: string;
  exclude?: string;
}

const CONFIG_FILE = ".pre-commit-config.yaml";

async function checkPreCommitInstalled(): Promise<boolean> {
  try {
    await $`pre-commit --version`.quiet();
    return true;
  } catch {
    return false;
  }
}

async function getPreCommitVersion(): Promise<string> {
  try {
    const result = await $`pre-commit --version`.text();
    return result.trim();
  } catch {
    return "Not installed";
  }
}

function loadConfig(): PreCommitConfig | null {
  if (!existsSync(CONFIG_FILE)) {
    console.error(`❌ ${CONFIG_FILE} not found`);
    return null;
  }

  try {
    const content = readFileSync(CONFIG_FILE, "utf-8");
    return parseYaml(content) as PreCommitConfig;
  } catch (error) {
    console.error(`❌ Failed to parse ${CONFIG_FILE}:`, error);
    return null;
  }
}

async function status(): Promise<void> {
  console.log("🔍 Pre-commit Status\n");

  // Check installation
  const installed = await checkPreCommitInstalled();
  const version = await getPreCommitVersion();

  console.log(`📦 Pre-commit: ${installed ? "✅ Installed" : "❌ Not installed"}`);
  console.log(`   Version: ${version}`);

  // Check config file
  const configExists = existsSync(CONFIG_FILE);
  console.log(`\n📄 Config: ${configExists ? "✅ Found" : "❌ Not found"}`);

  if (configExists) {
    const config = loadConfig();
    if (config) {
      console.log(`   Repositories: ${config.repos?.length || 0}`);

      const hookCount = config.repos?.reduce(
        (acc, repo) => acc + (repo.hooks?.length || 0),
        0
      ) || 0;
      console.log(`   Total Hooks: ${hookCount}`);

      if (config.default_stages) {
        console.log(`   Default Stages: ${config.default_stages.join(", ")}`);
      }
      if (config.fail_fast) {
        console.log(`   Fail Fast: enabled`);
      }
    }
  }

  // Check git hooks installation
  const gitHooksPath = ".git/hooks/pre-commit";
  const hooksInstalled = existsSync(gitHooksPath);
  console.log(`\n🪝 Git Hooks: ${hooksInstalled ? "✅ Installed" : "❌ Not installed"}`);

  if (!hooksInstalled && configExists) {
    console.log("\n💡 Run 'pre-commit install' to set up git hooks");
  }
}

async function install(options: { installHooks?: boolean }): Promise<void> {
  console.log("📦 Installing pre-commit hooks...\n");

  const installed = await checkPreCommitInstalled();
  if (!installed) {
    console.log("❌ pre-commit is not installed");
    console.log("💡 Install with: pip install pre-commit");
    process.exit(1);
  }

  if (!existsSync(CONFIG_FILE)) {
    console.log(`❌ ${CONFIG_FILE} not found`);
    console.log("💡 Create one with: pre-commit sample-config > .pre-commit-config.yaml");
    process.exit(1);
  }

  try {
    if (options.installHooks) {
      console.log("Installing hooks with dependencies...");
      await $`pre-commit install --install-hooks`;
    } else {
      await $`pre-commit install`;
    }
    console.log("\n✅ Pre-commit hooks installed successfully!");
  } catch (error) {
    console.error("❌ Failed to install hooks:", error);
    process.exit(1);
  }
}

async function run(options: {
  allFiles?: boolean;
  hookId?: string;
  files?: string[];
}): Promise<void> {
  const installed = await checkPreCommitInstalled();
  if (!installed) {
    console.error("❌ pre-commit is not installed");
    process.exit(1);
  }

  const args: string[] = ["run"];

  if (options.hookId) {
    args.push(options.hookId);
  }

  if (options.allFiles) {
    args.push("--all-files");
  }

  if (options.files && options.files.length > 0) {
    args.push("--files", ...options.files);
  }

  console.log(`🚀 Running: pre-commit ${args.join(" ")}\n`);

  try {
    const proc = Bun.spawn(["pre-commit", ...args], {
      stdout: "inherit",
      stderr: "inherit",
    });
    const exitCode = await proc.exited;
    process.exit(exitCode);
  } catch (error) {
    console.error("❌ Hook execution failed");
    process.exit(1);
  }
}

async function update(options: { bleedingEdge?: boolean }): Promise<void> {
  console.log("🔄 Updating pre-commit hooks...\n");

  const installed = await checkPreCommitInstalled();
  if (!installed) {
    console.error("❌ pre-commit is not installed");
    process.exit(1);
  }

  try {
    if (options.bleedingEdge) {
      await $`pre-commit autoupdate --bleeding-edge`;
    } else {
      await $`pre-commit autoupdate`;
    }
    console.log("\n✅ Hooks updated successfully!");
  } catch (error) {
    console.error("❌ Update failed:", error);
    process.exit(1);
  }
}

async function clean(): Promise<void> {
  console.log("🧹 Cleaning pre-commit cache...\n");

  const installed = await checkPreCommitInstalled();
  if (!installed) {
    console.error("❌ pre-commit is not installed");
    process.exit(1);
  }

  try {
    await $`pre-commit clean`;
    console.log("✅ Cache cleaned successfully!");
  } catch (error) {
    console.error("❌ Clean failed:", error);
    process.exit(1);
  }
}

function validate(): void {
  console.log("🔍 Validating pre-commit configuration...\n");

  const config = loadConfig();
  if (!config) {
    process.exit(1);
  }

  const issues: string[] = [];
  const warnings: string[] = [];

  // Validate repos
  if (!config.repos || config.repos.length === 0) {
    issues.push("No repositories defined");
  } else {
    config.repos.forEach((repo, index) => {
      // Check repo URL
      if (!repo.repo) {
        issues.push(`Repo ${index + 1}: Missing 'repo' field`);
      }

      // Check rev (warn if using branch-like names)
      if (!repo.rev) {
        issues.push(`Repo ${index + 1}: Missing 'rev' field`);
      } else if (!repo.rev.startsWith("v") && !repo.rev.match(/^[a-f0-9]{7,40}$/)) {
        if (repo.repo !== "local" && repo.repo !== "meta") {
          warnings.push(
            `Repo ${index + 1} (${repo.repo}): 'rev' should be a version tag or commit SHA, not '${repo.rev}'`
          );
        }
      }

      // Check hooks
      if (!repo.hooks || repo.hooks.length === 0) {
        issues.push(`Repo ${index + 1}: No hooks defined`);
      } else {
        repo.hooks.forEach((hook, hookIndex) => {
          if (!hook.id) {
            issues.push(`Repo ${index + 1}, Hook ${hookIndex + 1}: Missing 'id' field`);
          }
        });
      }
    });
  }

  // Report results
  if (issues.length > 0) {
    console.log("❌ Errors:");
    issues.forEach((issue) => console.log(`   - ${issue}`));
  }

  if (warnings.length > 0) {
    console.log("\n⚠️  Warnings:");
    warnings.forEach((warning) => console.log(`   - ${warning}`));
  }

  if (issues.length === 0 && warnings.length === 0) {
    console.log("✅ Configuration is valid!");
  }

  // Summary
  console.log("\n📊 Summary:");
  console.log(`   Repositories: ${config.repos?.length || 0}`);
  const hookCount =
    config.repos?.reduce((acc, repo) => acc + (repo.hooks?.length || 0), 0) || 0;
  console.log(`   Total Hooks: ${hookCount}`);

  if (issues.length > 0) {
    process.exit(1);
  }
}

function listHooks(): void {
  console.log("📋 Configured Hooks\n");

  const config = loadConfig();
  if (!config) {
    process.exit(1);
  }

  config.repos?.forEach((repo) => {
    const repoName =
      repo.repo === "local"
        ? "local"
        : repo.repo === "meta"
          ? "meta"
          : repo.repo.split("/").slice(-2).join("/");

    console.log(`\n📦 ${repoName} (${repo.rev})`);

    repo.hooks?.forEach((hook) => {
      const name = hook.name || hook.id;
      const stages = hook.stages?.join(", ") || "pre-commit";
      console.log(`   └─ ${hook.id}`);
      if (hook.name && hook.name !== hook.id) {
        console.log(`      Name: ${hook.name}`);
      }
      if (hook.files) {
        console.log(`      Files: ${hook.files}`);
      }
      if (hook.stages) {
        console.log(`      Stages: ${stages}`);
      }
      if (hook.args && hook.args.length > 0) {
        console.log(`      Args: ${hook.args.join(" ")}`);
      }
    });
  });
}

function showHelp(): void {
  console.log(`
Pre-commit Manager - CLI for managing pre-commit configurations

Usage:
  bun run PreCommitManager.ts <command> [options]

Commands:
  status              Show pre-commit installation status
  install             Install pre-commit hooks
    --install-hooks   Also download hook dependencies
  run [hook-id]       Run hooks
    --all-files       Run on all files
    --files <files>   Run on specific files
  update              Update hooks to latest versions
    --bleeding-edge   Use latest commits instead of tags
  clean               Clean cached environments
  validate            Validate configuration file
  list                List configured hooks
  help                Show this help message

Examples:
  bun run PreCommitManager.ts status
  bun run PreCommitManager.ts install --install-hooks
  bun run PreCommitManager.ts run --all-files
  bun run PreCommitManager.ts run black
  bun run PreCommitManager.ts update
  bun run PreCommitManager.ts validate
`);
}

// Main CLI
async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const command = args[0];

  switch (command) {
    case "status":
      await status();
      break;

    case "install":
      await install({
        installHooks: args.includes("--install-hooks"),
      });
      break;

    case "run":
      const hookId = args[1] && !args[1].startsWith("--") ? args[1] : undefined;
      const allFiles = args.includes("--all-files");
      const filesIndex = args.indexOf("--files");
      const files =
        filesIndex > -1 ? args.slice(filesIndex + 1).filter((a) => !a.startsWith("--")) : [];

      await run({ allFiles, hookId, files });
      break;

    case "update":
      await update({
        bleedingEdge: args.includes("--bleeding-edge"),
      });
      break;

    case "clean":
      await clean();
      break;

    case "validate":
      validate();
      break;

    case "list":
      listHooks();
      break;

    case "help":
    case "--help":
    case "-h":
      showHelp();
      break;

    default:
      if (command) {
        console.error(`Unknown command: ${command}\n`);
      }
      showHelp();
      process.exit(command ? 1 : 0);
  }
}

main().catch(console.error);
