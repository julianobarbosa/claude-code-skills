#!/usr/bin/env npx tsx
/**
 * c7-resolve - Resolve library name to Context7 library ID
 *
 * Usage: npx tsx resolve.ts <library_name> [query]
 *
 * Examples:
 *   npx tsx resolve.ts react
 *   npx tsx resolve.ts next.js "app router authentication"
 *   CONTEXT7_API_KEY=ctx7sk_xxx npx tsx resolve.ts kubernetes
 */

import { Context7Client, log, getKnownLibraryId, COMMON_LIBRARIES } from "../lib/context7.js";

function printUsage(): void {
  console.log(`
Usage: npx tsx resolve.ts <library_name> [query]

Resolve a library name to a Context7-compatible library ID.

Arguments:
  library_name    Name of the library (e.g., "react", "next.js", "kubernetes")
  query           Optional context query for LLM-powered ranking

Environment Variables:
  CONTEXT7_API_KEY    Optional API key for higher rate limits (get at context7.com/dashboard)

Examples:
  npx tsx resolve.ts react
  npx tsx resolve.ts next.js "server components"
  npx tsx resolve.ts kubernetes "deployment spec"

Common Library IDs (no API call needed):
${Object.entries(COMMON_LIBRARIES)
  .slice(0, 10)
  .map(([name, id]) => `  ${name.padEnd(15)} -> ${id}`)
  .join("\n")}
  ...and more
`);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);

  if (args.length === 0 || args[0] === "--help" || args[0] === "-h") {
    printUsage();
    process.exit(args.length === 0 ? 1 : 0);
  }

  const libraryName = args[0];
  const query = args[1];

  // Check if we have a known ID first
  const knownId = getKnownLibraryId(libraryName);
  if (knownId && !query) {
    log("info", `Using known library ID for '${libraryName}'`);
    console.log(`\nLibrary ID: ${knownId}`);
    console.log(`\nTip: Use this ID with 'npx tsx query.ts "${knownId}" "your query"'`);
    return;
  }

  try {
    const client = new Context7Client();
    const result = await client.resolveLibrary(libraryName, query);

    if (!result.bestMatch) {
      console.log("\nNo libraries found.");
      if (knownId) {
        console.log(`\nHowever, a known ID exists: ${knownId}`);
      }
      process.exit(1);
    }

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
    console.log(`\nTip: Use this ID with 'npx tsx query.ts "${result.bestMatch.id}" "your query"'`);
  } catch (error) {
    log("error", error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

main();
