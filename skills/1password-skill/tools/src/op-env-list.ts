#!/usr/bin/env bun
/**
 * op-env-list - List environment items from 1Password
 *
 * Usage:
 *   op-env-list [--vault <vault>] [--tags <tags>]
 */

import { parseArgs } from "util";
import {
  log,
  colors,
  ensureAuth,
  listEnvironments,
} from "./utils";

const HELP = `
op-env-list - List environment items from 1Password

USAGE:
    op-env-list [OPTIONS]

OPTIONS:
    --vault <vault>   Filter by vault name
    --tags <tags>     Filter by tags (comma-separated, default: environment)
    --json            Output in JSON format
    --help            Show this help message

EXAMPLES:
    # List all environments
    op-env-list

    # Filter by vault
    op-env-list --vault Development

    # Filter by tags
    op-env-list --tags environment,production

    # JSON output
    op-env-list --json
`;

async function main() {
  const { values } = parseArgs({
    args: Bun.argv.slice(2),
    options: {
      vault: { type: "string" },
      tags: { type: "string", default: "environment" },
      json: { type: "boolean" },
      help: { type: "boolean", short: "h" },
    },
    allowPositionals: true,
  });

  if (values.help) {
    console.log(HELP);
    process.exit(0);
  }

  await ensureAuth();

  // Get environments
  const items = await listEnvironments(values.vault, values.tags);

  // JSON output mode
  if (values.json) {
    console.log(JSON.stringify(items, null, 2));
    process.exit(0);
  }

  if (items.length === 0) {
    console.log("No environments found");
    console.log();
    console.log("Tip: Create one with: op-env-create <name> <vault> KEY=value");
    process.exit(0);
  }

  const c = colors.cyan;

  console.log();
  console.log(c("╔═══════════════════════════════════════════════════════════════════════════════╗"));
  console.log(`${c("║")}                           1Password Environments                              ${c("║")}`);
  console.log(c("╠═══════════════════════════════════════════════════════════════════════════════╣"));

  // Header
  const nameHeader = "NAME".padEnd(35);
  const vaultHeader = "VAULT".padEnd(20);
  const updatedHeader = "UPDATED".padEnd(15);
  console.log(`${c("║")} ${nameHeader} │ ${vaultHeader} │ ${updatedHeader} ${c("║")}`);
  console.log(c("╠═══════════════════════════════════════════════════════════════════════════════╣"));

  // Items
  for (const item of items) {
    const title = (item.title || "").substring(0, 35).padEnd(35);
    const vault = (item.vault?.name || "").substring(0, 20).padEnd(20);
    const updated = (item.updated_at || "N/A").substring(0, 10).padEnd(15);
    console.log(`${c("║")} ${title} │ ${vault} │ ${updated} ${c("║")}`);
  }

  console.log(c("╚═══════════════════════════════════════════════════════════════════════════════╝"));
  console.log();
  console.log(`Total: ${items.length} environments`);
  console.log();
  console.log("Commands:");
  console.log("  Show details: op-env-show <name> <vault>");
  console.log("  Export .env:  op-env-export <name> <vault> > .env");
}

main().catch((err) => {
  log.error(err.message);
  process.exit(1);
});
