#!/usr/bin/env bun
/**
 * c7-query — Query documentation for a known library ID.
 *
 * Usage:
 *   c7-query <library_id> <query> [flags]
 *   bun src/cli/query.ts <library_id> <query> [flags]
 *
 * Examples:
 *   c7-query /facebook/react "useEffect cleanup function"
 *   c7-query /vercel/next.js "app router middleware" --json
 *   c7-query /kubernetes/kubernetes "deployment spec" --quiet
 */

import { Context7Client, COMMON_LIBRARIES, log, setLogLevel } from "../lib/context7.js";
import { parseArgs } from "../lib/flags.js";
import { formatError } from "../lib/errors.js";
import pkg from "../../package.json" with { type: "json" };

function printUsage(): void {
  console.log(`
Usage: c7-query <library_id> <query> [flags]

Query up-to-date documentation from Context7 by library ID.

Arguments:
  library_id        Context7 library ID, must start with '/' (e.g., "/facebook/react")
  query             Natural language question about the library

Flags:
  --json            Emit JSON to stdout; suppress decorative output
  --quiet, -q       Suppress info/success logs
  --timeout <ms>    HTTP timeout (default 30000)
  --max-retries <n> Max retries on 429 (default 1)
  --api-key <key>   Override CONTEXT7_API_KEY
  --version, -V     Print version and exit
  --help, -h        This help

Common library IDs:
${Object.entries(COMMON_LIBRARIES).slice(0, 8).map(([name, id]) => `  ${id.padEnd(25)} (${name})`).join("\n")}

Tip: Use 'c7-resolve <name>' to find unfamiliar library IDs.
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

  if (positional.length < 2) {
    printUsage();
    process.exit(1);
  }

  if (flags.quiet || flags.json) setLogLevel(flags.json ? "warn" : "silent");

  const libraryId = positional[0]!;
  const query = positional.slice(1).join(" ");

  if (!libraryId.startsWith("/")) {
    process.stderr.write(`Error: Invalid library ID format: ${libraryId}\n`);
    process.stderr.write(`Hint: Library ID must start with '/' (e.g., '/facebook/react'). Run c7-resolve first.\n`);
    process.exit(4);
  }

  try {
    const client = new Context7Client({
      apiKey: flags.apiKey,
      timeout: flags.timeoutMs,
      maxRetries: flags.maxRetries,
    });

    const result = await client.queryDocs(libraryId, query);

    if (flags.json) {
      process.stdout.write(
        JSON.stringify({ libraryId: result.libraryId, query: result.query, rawContent: result.rawContent }, null, 2) + "\n"
      );
    } else {
      console.log("\n" + "=".repeat(80));
      console.log(`Library: ${result.libraryId}`);
      console.log(`Query: ${result.query}`);
      console.log("=".repeat(80) + "\n");

      if (result.rawContent) {
        console.log(result.rawContent);
      } else if (result.snippets.length > 0) {
        result.snippets.forEach((snippet, index) => {
          console.log(`--- Snippet ${index + 1} ---`);
          if (snippet.title) console.log(`Title: ${snippet.title}`);
          console.log(snippet.content);
          if (snippet.url) console.log(`Source: ${snippet.url}`);
          console.log();
        });
      } else {
        console.log("No documentation found for this query.");
        console.log("\nTips:");
        console.log("  - Try a more specific query");
        console.log("  - Try broader terms");
        console.log("  - Check if the library ID is correct (run c7-resolve)");
      }
      console.log("\n" + "=".repeat(80));
    }
  } catch (err) {
    const f = formatError(err);
    process.stderr.write(`Error: ${f.message}\n`);
    if (f.hint) process.stderr.write(`Hint: ${f.hint}\n`);
    process.exit(f.exitCode);
  }
}

main();
