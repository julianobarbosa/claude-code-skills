#!/usr/bin/env bun
/**
 * op-env-update - Update environment item in 1Password
 *
 * Usage:
 *   op-env-update <name> <vault> [--from-file <.env>] [--remove <keys>] [key=value...]
 */

import { parseArgs } from "util";
import {
  log,
  ensureAuth,
  itemExists,
  parseEnvFile,
  parseInlineVars,
  updateEnvironment,
  deleteVariable,
} from "./utils";

const HELP = `
op-env-update - Update environment item in 1Password

USAGE:
    op-env-update <name> <vault> [OPTIONS] [key=value...]

ARGUMENTS:
    <name>      Name/title of the environment item
    <vault>     Vault containing the item

OPTIONS:
    --from-file <path>   Import/merge variables from .env file
    --remove <keys>      Comma-separated list of keys to remove
    --help               Show this help message

EXAMPLES:
    # Update single variable
    op-env-update my-app-dev Development API_KEY=new-key

    # Merge from .env file
    op-env-update my-app-prod Production --from-file .env.prod

    # Remove specific variables
    op-env-update azure-config Shared --remove OLD_KEY,DEPRECATED_VAR

    # Update and remove in one command
    op-env-update my-app Development NEW_KEY=value --remove OLD_KEY
`;

async function main() {
  const { values, positionals } = parseArgs({
    args: Bun.argv.slice(2),
    options: {
      "from-file": { type: "string" },
      remove: { type: "string" },
      help: { type: "boolean", short: "h" },
    },
    allowPositionals: true,
  });

  if (values.help) {
    console.log(HELP);
    process.exit(0);
  }

  // Parse positionals
  const envVars: string[] = [];
  let name = "";
  let vault = "";

  for (const arg of positionals) {
    if (arg.includes("=")) {
      envVars.push(arg);
    } else if (!name) {
      name = arg;
    } else if (!vault) {
      vault = arg;
    }
  }

  if (!name || !vault) {
    log.error("Missing required arguments: name and vault");
    console.log(HELP);
    process.exit(1);
  }

  await ensureAuth();

  // Check if item exists
  if (!(await itemExists(name, vault))) {
    log.error(`Item '${name}' not found in vault '${vault}'`);
    log.info("Use op-env-create to create a new environment");
    process.exit(1);
  }

  log.info(`Updating environment: ${name} in vault: ${vault}`);

  // Handle removals first
  if (values.remove) {
    const keysToRemove = values.remove.split(",").map((k) => k.trim());
    for (const key of keysToRemove) {
      log.info(`Removing variable: ${key}`);
      await deleteVariable(name, vault, key);
    }
  }

  // Collect variables to update
  const vars = new Map<string, string>();

  if (values["from-file"]) {
    const filePath = values["from-file"];
    const file = Bun.file(filePath);

    if (!(await file.exists())) {
      log.error(`File not found: ${filePath}`);
      process.exit(1);
    }

    log.info(`Loading variables from: ${filePath}`);
    const content = await file.text();
    const fileVars = parseEnvFile(content);
    for (const [k, v] of fileVars) {
      vars.set(k, v);
    }
  }

  // Add inline variables
  const inlineVars = parseInlineVars(envVars);
  for (const [k, v] of inlineVars) {
    vars.set(k, v);
  }

  // Apply updates
  if (vars.size > 0) {
    log.info(`Updating variables: ${Array.from(vars.keys()).join(" ")}`);

    const success = await updateEnvironment(name, vault, vars);
    if (success) {
      log.info(`Environment '${name}' updated successfully`);
    } else {
      log.error("Failed to update environment");
      process.exit(1);
    }
  } else if (!values.remove) {
    log.warn("No variables to update");
  } else {
    log.info("Removal complete");
  }

  console.log("\nCurrent state:");
  console.log(`  op-env-show '${name}' '${vault}'`);
}

main().catch((err) => {
  log.error(err.message);
  process.exit(1);
});
