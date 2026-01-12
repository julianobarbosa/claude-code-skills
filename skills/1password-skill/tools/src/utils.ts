/**
 * Shared utilities for 1Password environment tools
 */

import { $ } from "bun";

// Colors for terminal output
export const colors = {
  red: (s: string) => `\x1b[31m${s}\x1b[0m`,
  green: (s: string) => `\x1b[32m${s}\x1b[0m`,
  yellow: (s: string) => `\x1b[33m${s}\x1b[0m`,
  cyan: (s: string) => `\x1b[36m${s}\x1b[0m`,
  bold: (s: string) => `\x1b[1m${s}\x1b[0m`,
};

export const log = {
  info: (msg: string) => console.log(`${colors.green("[INFO]")} ${msg}`),
  warn: (msg: string) => console.log(`${colors.yellow("[WARN]")} ${msg}`),
  error: (msg: string) => console.error(`${colors.red("[ERROR]")} ${msg}`),
};

/**
 * Check if op CLI is installed
 */
export async function checkOpCli(): Promise<boolean> {
  try {
    await $`which op`.quiet();
    return true;
  } catch {
    return false;
  }
}

/**
 * Check if user is signed in to 1Password
 */
export async function isSignedIn(): Promise<boolean> {
  try {
    await $`op whoami`.quiet();
    return true;
  } catch {
    return false;
  }
}

/**
 * Ensure op CLI is available and user is signed in
 */
export async function ensureAuth(): Promise<void> {
  if (!(await checkOpCli())) {
    log.error("1Password CLI (op) not found. Install from: https://developer.1password.com/docs/cli");
    process.exit(1);
  }

  if (!(await isSignedIn())) {
    log.error("Not signed in to 1Password. Run: op signin");
    process.exit(1);
  }
}

/**
 * Check if an item exists in a vault
 */
export async function itemExists(name: string, vault: string): Promise<boolean> {
  try {
    await $`op item get ${name} --vault ${vault}`.quiet();
    return true;
  } catch {
    return false;
  }
}

/**
 * List all vaults
 */
export async function listVaults(): Promise<string[]> {
  try {
    const result = await $`op vault list --format=json`.json();
    return result.map((v: { name: string }) => v.name);
  } catch {
    return [];
  }
}

/**
 * Parse .env file content into key-value pairs
 */
export function parseEnvFile(content: string): Map<string, string> {
  const vars = new Map<string, string>();

  for (const line of content.split("\n")) {
    // Skip comments and empty lines
    if (line.trim().startsWith("#") || !line.trim()) continue;

    // Parse KEY=VALUE
    const match = line.match(/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/);
    if (match) {
      const [, key, rawValue] = match;
      // Remove surrounding quotes
      let value = rawValue;
      if ((value.startsWith('"') && value.endsWith('"')) ||
          (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      vars.set(key, value);
    }
  }

  return vars;
}

/**
 * Parse KEY=VALUE arguments into a Map
 */
export function parseInlineVars(args: string[]): Map<string, string> {
  const vars = new Map<string, string>();

  for (const arg of args) {
    const match = arg.match(/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/);
    if (match) {
      vars.set(match[1], match[2]);
    }
  }

  return vars;
}

/**
 * Get item details as JSON
 */
export async function getItem(name: string, vault: string, reveal = false): Promise<any> {
  try {
    const args = ["op", "item", "get", name, "--vault", vault, "--format", "json"];
    if (reveal) args.push("--reveal");

    const proc = Bun.spawn(args, { stdout: "pipe" });
    const output = await new Response(proc.stdout).text();
    return JSON.parse(output);
  } catch {
    return null;
  }
}

/**
 * Create an environment item in 1Password
 */
export async function createEnvironment(
  name: string,
  vault: string,
  vars: Map<string, string>,
  tags = "environment"
): Promise<boolean> {
  const fieldArgs: string[] = [];

  for (const [key, value] of vars) {
    fieldArgs.push(`variables.${key}[concealed]=${value}`);
  }

  try {
    const args = [
      "op", "item", "create",
      "--category", "API Credential",
      "--title", name,
      "--vault", vault,
      "--tags", tags,
      ...fieldArgs,
    ];

    const proc = Bun.spawn(args, { stdout: "pipe", stderr: "pipe" });
    const exitCode = await proc.exited;
    return exitCode === 0;
  } catch {
    return false;
  }
}

/**
 * Update an environment item in 1Password
 */
export async function updateEnvironment(
  name: string,
  vault: string,
  vars: Map<string, string>
): Promise<boolean> {
  if (vars.size === 0) return true;

  const fieldArgs: string[] = [];
  for (const [key, value] of vars) {
    fieldArgs.push(`variables.${key}[concealed]=${value}`);
  }

  try {
    const args = ["op", "item", "edit", name, "--vault", vault, ...fieldArgs];
    const proc = Bun.spawn(args, { stdout: "pipe", stderr: "pipe" });
    const exitCode = await proc.exited;
    return exitCode === 0;
  } catch {
    return false;
  }
}

/**
 * Delete a variable from an environment
 */
export async function deleteVariable(name: string, vault: string, key: string): Promise<boolean> {
  try {
    const args = ["op", "item", "edit", name, "--vault", vault, `variables.${key}[delete]`];
    const proc = Bun.spawn(args, { stdout: "pipe", stderr: "pipe" });
    await proc.exited;
    return true;
  } catch {
    return false;
  }
}

/**
 * Delete an environment item
 */
export async function deleteEnvironment(
  name: string,
  vault: string,
  archive = false
): Promise<boolean> {
  try {
    const args = ["op", "item", "delete", name, "--vault", vault];
    if (archive) args.push("--archive");

    const proc = Bun.spawn(args, { stdout: "pipe", stderr: "pipe" });
    const exitCode = await proc.exited;
    return exitCode === 0;
  } catch {
    return false;
  }
}

/**
 * List items with a specific tag
 */
export async function listEnvironments(vault?: string, tags = "environment"): Promise<any[]> {
  try {
    const args = ["op", "item", "list", "--tags", tags, "--format", "json"];
    if (vault) {
      args.push("--vault", vault);
    }

    const proc = Bun.spawn(args, { stdout: "pipe" });
    const output = await new Response(proc.stdout).text();
    return JSON.parse(output || "[]");
  } catch {
    return [];
  }
}

/**
 * Extract variables from an item's fields
 */
export function extractVariables(item: any): Map<string, string> {
  const vars = new Map<string, string>();

  if (!item?.fields) return vars;

  for (const field of item.fields) {
    // Check if field is in 'variables' section
    const sectionLabel = field.section?.label || field.section?.id || "";
    if (sectionLabel === "variables" || field.type === "CONCEALED") {
      if (field.label) {
        vars.set(field.label, field.value || "");
      }
    }
  }

  return vars;
}

/**
 * Read a single secret
 */
export async function readSecret(vault: string, item: string, field: string): Promise<string | null> {
  try {
    const ref = `op://${vault}/${item}/variables/${field}`;
    const proc = Bun.spawn(["op", "read", ref], { stdout: "pipe" });
    const output = await new Response(proc.stdout).text();
    return output.trim();
  } catch {
    return null;
  }
}
