#!/usr/bin/env bun
/**
 * op-env-export - Export environment to .env file format
 *
 * Usage:
 *   op-env-export <name> <vault> [--format <format>] > .env
 */

import { parseArgs } from "util";
import {
  log,
  ensureAuth,
  itemExists,
  getItem,
  extractVariables,
  readSecret,
} from "./utils";

const HELP = `
op-env-export - Export environment to .env file format

USAGE:
    op-env-export <name> <vault> [OPTIONS]

ARGUMENTS:
    <name>      Name/title of the environment item
    <vault>     Vault containing the item

OPTIONS:
    --format <fmt>   Output format (default: env)
                     - env: Standard KEY=value format
                     - docker: Docker-compatible with quotes
                     - op-refs: Use op:// references (for templates)
                     - json: JSON key-value object
    --prefix <str>   Add prefix to all variable names
    --help           Show this help message

EXAMPLES:
    # Export to .env file
    op-env-export my-app-dev Development > .env

    # Docker-compatible format
    op-env-export my-app Development --format docker > .env

    # Create template with op:// references
    op-env-export my-app-prod Production --format op-refs > .env.tpl

    # JSON format
    op-env-export config Shared --format json

    # Add prefix to all variables
    op-env-export azure Shared --prefix AZURE_ > .env
`;

type ExportFormat = "env" | "docker" | "op-refs" | "json";

async function main() {
  const { values, positionals } = parseArgs({
    args: Bun.argv.slice(2),
    options: {
      format: { type: "string", default: "env" },
      prefix: { type: "string", default: "" },
      help: { type: "boolean", short: "h" },
    },
    allowPositionals: true,
  });

  if (values.help) {
    console.log(HELP);
    process.exit(0);
  }

  const [name, vault] = positionals;

  if (!name || !vault) {
    log.error("Missing required arguments: name and vault");
    console.log(HELP);
    process.exit(1);
  }

  const format = values.format as ExportFormat;
  const prefix = values.prefix || "";

  if (!["env", "docker", "op-refs", "json"].includes(format)) {
    log.error(`Unknown format: ${format}`);
    log.error("Supported formats: env, docker, op-refs, json");
    process.exit(1);
  }

  await ensureAuth();

  // Check if item exists
  if (!(await itemExists(name, vault))) {
    log.error(`Item '${name}' not found in vault '${vault}'`);
    process.exit(1);
  }

  log.info(`Exporting: ${name} from ${vault} (format: ${format})`);

  // Get item with revealed values
  const item = await getItem(name, vault, true);

  if (!item) {
    log.error("Failed to retrieve item");
    process.exit(1);
  }

  // Extract variables
  const vars = extractVariables(item);

  if (vars.size === 0) {
    log.error("No variables found in environment");
    process.exit(1);
  }

  // Get revealed values for each variable
  const revealedVars = new Map<string, string>();
  for (const [key] of vars) {
    const value = await readSecret(vault, name, key) || vars.get(key) || "";
    revealedVars.set(key, value);
  }

  // Output header comment
  const timestamp = new Date().toISOString();

  switch (format) {
    case "env":
    case "docker":
      console.log(`# Generated from 1Password: ${name} (${vault})`);
      console.log(`# Date: ${timestamp}`);
      console.log();
      break;
    case "op-refs":
      console.log(`# 1Password Template: ${name} (${vault})`);
      console.log(`# Use with: op inject -i .env.tpl -o .env`);
      console.log(`# Or: op run --env-file .env.tpl -- command`);
      console.log();
      break;
  }

  // Output variables
  switch (format) {
    case "env":
      for (const [key, value] of revealedVars) {
        const escaped = value.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
        console.log(`${prefix}${key}=${escaped}`);
      }
      break;

    case "docker":
      for (const [key, value] of revealedVars) {
        const escaped = value.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
        console.log(`${prefix}${key}="${escaped}"`);
      }
      break;

    case "op-refs":
      for (const [key] of revealedVars) {
        console.log(`${prefix}${key}=op://${vault}/${name}/variables/${key}`);
      }
      break;

    case "json":
      const obj: Record<string, string> = {};
      for (const [key, value] of revealedVars) {
        obj[`${prefix}${key}`] = value;
      }
      console.log(JSON.stringify(obj, null, 2));
      break;
  }

  log.info("Export complete");
}

main().catch((err) => {
  log.error(err.message);
  process.exit(1);
});
