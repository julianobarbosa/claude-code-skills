#!/usr/bin/env bun
/**
 * c7-resolve — Resolve library name to Context7 library ID.
 *
 * Usage:
 *   c7-resolve <library_name> [query] [flags]
 *   bun src/cli/resolve.ts <library_name> [query] [flags]
 *
 * Examples:
 *   c7-resolve react
 *   c7-resolve next.js "app router authentication"
 *   c7-resolve kubernetes --json
 */

import {
  Context7Client,
  COMMON_LIBRARIES,
  getKnownLibraryId,
  log,
  setLogLevel,
} from "../lib/context7.js";
import { parseArgs } from "../lib/flags.js";
import { formatError } from "../lib/errors.js";
import { getCached, setCached, clearCache } from "../lib/cache.js";
import pkg from "../../package.json" with { type: "json" };

const CACHE_TTL_MS = 24 * 60 * 60 * 1000;

function printUsage(): void {
  console.log(`
Usage: c7-resolve <library_name> [query] [flags]

Resolve a library name to a Context7-compatible library ID.

Arguments:
  library_name      Name of the library (e.g., "react", "next.js", "kubernetes")
  query             Optional context query for LLM-powered ranking

Flags:
  --json            Emit JSON to stdout; suppress decorative output
  --quiet, -q       Suppress info/success logs
  --no-cache        Bypass the disk cache for this call
  --clear-cache     Remove the disk cache and exit
  --timeout <ms>    HTTP timeout (default 30000)
  --max-retries <n> Max retries on 429 (default 1)
  --api-key <key>   Override CONTEXT7_API_KEY
  --version, -V     Print version and exit
  --help, -h        This help

Common shortcuts (skip API call):
${Object.entries(COMMON_LIBRARIES).slice(0, 10).map(([n, id]) => `  ${n.padEnd(15)} -> ${id}`).join("\n")}
  ...and more

Examples:
  c7-resolve react
  c7-resolve next.js "server components"
  c7-resolve unknown-lib --json
`);
}

async function main(): Promise<void> {
  let parsed;
  try {
    parsed = parseArgs(process.argv.slice(2));
  } catch (err) {
    const f = formatError(err);
    process.stderr.write(`Error: ${f.message}\n`);
    if (f.hint) process.stderr.write(`Hint: ${f.hint}\n`);
    process.exit(f.exitCode);
  }

  const { positional, flags } = parsed;

  if (flags.help) { printUsage(); process.exit(0); }
  if (flags.version) { console.log(pkg.version); process.exit(0); }

  if (flags.clearCache) {
    await clearCache();
    if (!flags.quiet) log("success", "Cache cleared");
    if (positional.length === 0) process.exit(0);
  }

  if (positional.length === 0) {
    printUsage();
    process.exit(1);
  }

  if (flags.quiet || flags.json) setLogLevel(flags.json ? "warn" : "silent");

  const libraryName = positional[0]!;
  const query = positional[1];

  try {
    // Cache and known-IDs short-circuit only when there's no extra query context.
    if (!query) {
      const cached = flags.noCache ? null : await getCached(libraryName, CACHE_TTL_MS);
      if (cached) {
        log("info", `Cache hit for '${libraryName}'`);
        if (flags.json) {
          process.stdout.write(JSON.stringify({ libraryName, bestMatch: { id: cached }, source: "cache" }, null, 2) + "\n");
        } else {
          console.log(`\nLibrary ID: ${cached}`);
          console.log(`\nTip: c7-query "${cached}" "your query"`);
        }
        return;
      }
      const knownId = getKnownLibraryId(libraryName);
      if (knownId) {
        log("info", `Using known library ID for '${libraryName}'`);
        if (flags.json) {
          process.stdout.write(JSON.stringify({ libraryName, bestMatch: { id: knownId }, source: "known" }, null, 2) + "\n");
        } else {
          console.log(`\nLibrary ID: ${knownId}`);
          console.log(`\nTip: c7-query "${knownId}" "your query"`);
        }
        return;
      }
    }

    const client = new Context7Client({
      apiKey: flags.apiKey,
      timeout: flags.timeoutMs,
      maxRetries: flags.maxRetries,
    });

    const result = await client.resolveLibrary(libraryName, query);

    if (!result.bestMatch) {
      if (flags.json) {
        process.stdout.write(JSON.stringify({ libraryName, libraries: [], bestMatch: null, source: "resolved" }, null, 2) + "\n");
      } else {
        console.log("\nNo libraries found.");
      }
      process.exit(4);
    }

    if (!flags.noCache) await setCached(libraryName, result.bestMatch.id);

    if (flags.json) {
      process.stdout.write(
        JSON.stringify(
          { libraryName, libraries: result.libraries, bestMatch: result.bestMatch, source: "resolved" },
          null,
          2
        ) + "\n"
      );
    } else {
      console.log("\n--- Results ---\n");
      result.libraries.slice(0, 5).forEach((lib, index) => {
        console.log(`[${index + 1}] ${lib.id}`);
        console.log(`    Name: ${lib.name || "N/A"}`);
        if (lib.description) {
          console.log(`    Description: ${lib.description.slice(0, 100)}${lib.description.length > 100 ? "..." : ""}`);
        }
        console.log();
      });
      console.log(`Best match: ${result.bestMatch.id}`);
      console.log(`\nTip: c7-query "${result.bestMatch.id}" "your query"`);
    }
  } catch (err) {
    const f = formatError(err);
    process.stderr.write(`Error: ${f.message}\n`);
    if (f.hint) process.stderr.write(`Hint: ${f.hint}\n`);
    process.exit(f.exitCode);
  }
}

main();
