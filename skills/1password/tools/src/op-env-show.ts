#!/usr/bin/env bun
/**
 * op-env-show - Display environment item details from 1Password
 *
 * Usage:
 *   op-env-show <name> <vault> [--reveal] [--json] [--keys]
 */

import { parseArgs } from "util";
import {
  log,
  colors,
  ensureAuth,
  itemExists,
  getItem,
  extractVariables,
  readSecret,
} from "./utils";

const HELP = `
op-env-show - Display environment item details from 1Password

USAGE:
    op-env-show <name> <vault> [OPTIONS]

ARGUMENTS:
    <name>      Name/title of the environment item
    <vault>     Vault containing the item

OPTIONS:
    --reveal    Show concealed values (default: masked)
    --json      Output in JSON format
    --keys      Show only variable names (no values)
    --help      Show this help message

EXAMPLES:
    # Show with masked values
    op-env-show my-app-dev Development

    # Show with revealed values
    op-env-show my-app-prod Production --reveal

    # JSON output
    op-env-show my-app-dev Development --json

    # List only variable names
    op-env-show azure-config Shared --keys
`;

async function main() {
  const { values, positionals } = parseArgs({
    args: Bun.argv.slice(2),
    options: {
      reveal: { type: "boolean", short: "r" },
      json: { type: "boolean" },
      keys: { type: "boolean" },
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

  // Get item data
  const item = await getItem(name, vault, values.reveal);

  if (!item) {
    log.error("Failed to retrieve item");
    process.exit(1);
  }

  // JSON output mode
  if (values.json) {
    console.log(JSON.stringify(item, null, 2));
    process.exit(0);
  }

  // Extract metadata
  const title = item.title || name;
  const vaultName = item.vault?.name || vault;
  const category = item.category || "Unknown";
  const created = item.created_at || "N/A";
  const updated = item.updated_at || "N/A";
  const tags = item.tags?.join(", ") || "none";

  // Display header
  const c = colors.cyan;
  console.log();
  console.log(c("╔═══════════════════════════════════════════════════════════════╗"));
  console.log(`${c("║")} Environment: ${colors.green(title)}`);
  console.log(c("╠═══════════════════════════════════════════════════════════════╣"));
  console.log(`${c("║")} Vault: ${vaultName}`);
  console.log(`${c("║")} Category: ${category}`);
  console.log(`${c("║")} Tags: ${tags}`);
  console.log(`${c("║")} Created: ${created}`);
  console.log(`${c("║")} Updated: ${updated}`);
  console.log(c("╠═══════════════════════════════════════════════════════════════╣"));
  console.log(`${c("║")} Variables:`);
  console.log(c("╚═══════════════════════════════════════════════════════════════╝"));
  console.log();

  // Extract and display variables
  const vars = extractVariables(item);

  if (vars.size === 0) {
    console.log("  (no variables found)");
  } else {
    for (const [key, value] of vars) {
      if (values.keys) {
        console.log(`  ${key}`);
      } else if (values.reveal) {
        // Get revealed value
        const revealedValue = await readSecret(vault, name, key) || value;
        console.log(`  ${key}=${revealedValue}`);
      } else {
        // Mask the value
        const masked = value ? "********" : "(empty)";
        console.log(`  ${key}=${masked}`);
      }
    }
  }

  console.log();
  if (!values.reveal && !values.keys) {
    console.log("Tip: Use --reveal to show actual values");
  }
}

main().catch((err) => {
  log.error(err.message);
  process.exit(1);
});
