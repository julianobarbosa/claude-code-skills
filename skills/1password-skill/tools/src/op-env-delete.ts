#!/usr/bin/env bun
/**
 * op-env-delete - Delete environment item from 1Password
 *
 * Usage:
 *   op-env-delete <name> <vault> [--force] [--archive]
 */

import { parseArgs } from "util";
import {
  log,
  ensureAuth,
  itemExists,
  deleteEnvironment,
} from "./utils";

const HELP = `
op-env-delete - Delete environment item from 1Password

USAGE:
    op-env-delete <name> <vault> [OPTIONS]

ARGUMENTS:
    <name>      Name/title of the environment item
    <vault>     Vault containing the item

OPTIONS:
    --force     Skip confirmation prompt
    --archive   Archive instead of permanent delete
    --help      Show this help message

EXAMPLES:
    # Interactive deletion
    op-env-delete my-app-dev Development

    # Force delete without confirmation
    op-env-delete old-config Shared --force

    # Archive instead of delete
    op-env-delete deprecated-env Production --archive
`;

async function main() {
  const { values, positionals } = parseArgs({
    args: Bun.argv.slice(2),
    options: {
      force: { type: "boolean", short: "f" },
      archive: { type: "boolean" },
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

  await ensureAuth();

  // Check if item exists
  if (!(await itemExists(name, vault))) {
    log.error(`Item '${name}' not found in vault '${vault}'`);
    process.exit(1);
  }

  log.info("Environment to delete:");
  console.log(`  Name: ${name}`);
  console.log(`  Vault: ${vault}`);
  console.log();

  // Confirm unless force
  if (!values.force) {
    const action = values.archive ? "Archive" : "Permanently DELETE";
    process.stdout.write(`${action} this environment? [y/N] `);

    const reader = Bun.stdin.stream().getReader();
    const { value } = await reader.read();
    reader.releaseLock();

    const response = new TextDecoder().decode(value).trim().toLowerCase();
    if (response !== "y" && response !== "yes") {
      log.info("Cancelled");
      process.exit(0);
    }
  }

  // Delete or archive
  const success = await deleteEnvironment(name, vault, values.archive);

  if (success) {
    if (values.archive) {
      log.info(`Environment '${name}' archived successfully`);
    } else {
      log.info(`Environment '${name}' deleted permanently`);
    }
  } else {
    log.error("Failed to delete environment");
    process.exit(1);
  }
}

main().catch((err) => {
  log.error(err.message);
  process.exit(1);
});
