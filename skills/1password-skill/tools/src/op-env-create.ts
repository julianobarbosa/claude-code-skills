#!/usr/bin/env bun
/**
 * op-env-create - Create environment item in 1Password
 *
 * Usage:
 *   op-env-create <name> <vault> [--from-file <.env>] [key=value...]
 *
 * Examples:
 *   op-env-create my-app-dev Development API_KEY=xxx DB_HOST=localhost
 *   op-env-create my-app-prod Production --from-file .env.prod
 */

import { parseArgs } from "util";
import {
  log,
  ensureAuth,
  itemExists,
  parseEnvFile,
  parseInlineVars,
  createEnvironment,
} from "./utils";

const HELP = `
op-env-create - Create environment item in 1Password

USAGE:
    op-env-create <name> <vault> [OPTIONS] [key=value...]

ARGUMENTS:
    <name>      Name/title for the environment item
    <vault>     Vault to store the item in

OPTIONS:
    --from-file <path>   Import variables from .env file
    --tags <tags>        Comma-separated tags (default: environment)
    --help               Show this help message

EXAMPLES:
    # Create with inline variables
    op-env-create my-app-dev Development API_KEY=xxx DB_HOST=localhost

    # Create from .env file
    op-env-create my-app-prod Production --from-file .env.prod

    # Combine file and inline (inline overrides file)
    op-env-create azure-config Shared --from-file .env EXTRA_KEY=value

    # With custom tags
    op-env-create secrets DevOps --tags "env,production,api" KEY=value
`;

async function main() {
  const { values, positionals } = parseArgs({
    args: Bun.argv.slice(2),
    options: {
      "from-file": { type: "string" },
      tags: { type: "string", default: "environment" },
      help: { type: "boolean", short: "h" },
    },
    allowPositionals: true,
  });

  if (values.help) {
    console.log(HELP);
    process.exit(0);
  }

  // Parse positionals: name, vault, and key=value pairs
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

  // Ensure authenticated
  await ensureAuth();

  // Check if item already exists
  if (await itemExists(name, vault)) {
    log.error(`Item '${name}' already exists in vault '${vault}'`);
    log.info("Use op-env-update to modify existing environment");
    process.exit(1);
  }

  // Collect variables
  const vars = new Map<string, string>();

  // Load from file if specified
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

  // Add/override with inline variables
  const inlineVars = parseInlineVars(envVars);
  for (const [k, v] of inlineVars) {
    vars.set(k, v);
  }

  if (vars.size === 0) {
    log.error("No environment variables provided");
    log.info("Use --from-file <.env> or provide KEY=value pairs");
    process.exit(1);
  }

  log.info(`Creating environment: ${name} in vault: ${vault}`);
  log.info(`Variables (${vars.size}): ${Array.from(vars.keys()).join(" ")}`);

  // Create the environment
  const success = await createEnvironment(name, vault, vars, values.tags);

  if (success) {
    log.info(`Environment '${name}' created successfully`);
    console.log("\nVariables stored:");
    for (const key of vars.keys()) {
      console.log(`  - ${key}`);
    }
    console.log("\nUsage:");
    console.log(`  # Export to .env file`);
    console.log(`  op-env-export '${name}' '${vault}' > .env`);
    console.log();
    const firstKey = vars.keys().next().value;
    console.log(`  # Read single variable`);
    console.log(`  op read 'op://${vault}/${name}/variables/${firstKey}'`);
  } else {
    log.error("Failed to create environment");
    process.exit(1);
  }
}

main().catch((err) => {
  log.error(err.message);
  process.exit(1);
});
