#!/usr/bin/env npx tsx
/**
 * c7-query - Query documentation from Context7
 *
 * Usage: npx tsx query.ts <library_id> <query>
 *
 * Examples:
 *   npx tsx query.ts /facebook/react "useEffect cleanup function"
 *   npx tsx query.ts /vercel/next.js "app router middleware"
 *   npx tsx query.ts /kubernetes/kubernetes "deployment spec fields"
 */

import { Context7Client, log, COMMON_LIBRARIES } from "../lib/context7.js";

function printUsage(): void {
  console.log(`
Usage: npx tsx query.ts <library_id> <query>

Query up-to-date documentation from Context7.

Arguments:
  library_id    Context7 library ID (e.g., "/facebook/react", "/vercel/next.js")
  query         Natural language question about the library

Environment Variables:
  CONTEXT7_API_KEY    Optional API key for higher rate limits (get at context7.com/dashboard)

Examples:
  npx tsx query.ts /facebook/react "useEffect cleanup function"
  npx tsx query.ts /vercel/next.js "app router middleware"
  npx tsx query.ts /kubernetes/kubernetes "deployment spec fields"

Common Library IDs:
${Object.entries(COMMON_LIBRARIES)
  .slice(0, 8)
  .map(([name, id]) => `  ${id.padEnd(25)} (${name})`)
  .join("\n")}

Tip: Use 'npx tsx resolve.ts <name>' to find library IDs
`);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);

  if (args.length < 2 || args[0] === "--help" || args[0] === "-h") {
    printUsage();
    process.exit(args.length < 2 && args[0] !== "--help" && args[0] !== "-h" ? 1 : 0);
  }

  const libraryId = args[0];
  const query = args.slice(1).join(" ");

  // Validate library ID format
  if (!libraryId.startsWith("/")) {
    log("error", `Invalid library ID format: ${libraryId}`);
    log("info", "Library ID should start with '/' (e.g., '/facebook/react')");
    process.exit(1);
  }

  try {
    const client = new Context7Client();
    const result = await client.queryDocs(libraryId, query);

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
      console.log("  - Check if the library ID is correct");
    }

    console.log("\n" + "=".repeat(80));
  } catch (error) {
    log("error", error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

main();
