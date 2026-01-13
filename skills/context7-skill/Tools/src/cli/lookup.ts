#!/usr/bin/env npx tsx
/**
 * c7-lookup - Full documentation lookup (resolve + query in one command)
 *
 * Usage: npx tsx lookup.ts <library_name> <query>
 *
 * Examples:
 *   npx tsx lookup.ts react "useEffect cleanup function"
 *   npx tsx lookup.ts next.js "app router middleware"
 *   npx tsx lookup.ts kubernetes "deployment spec fields"
 */

import { Context7Client, log, getKnownLibraryId, COMMON_LIBRARIES } from "../lib/context7.js";

function printUsage(): void {
  console.log(`
Usage: npx tsx lookup.ts <library_name> <query>

Full documentation lookup - resolves library and queries docs in one command.

Arguments:
  library_name    Name of the library (e.g., "react", "next.js", "kubernetes")
  query           Natural language question about the library

Environment Variables:
  CONTEXT7_API_KEY    Optional API key for higher rate limits (get at context7.com/dashboard)

Examples:
  npx tsx lookup.ts react "useEffect cleanup function"
  npx tsx lookup.ts next.js "app router middleware authentication"
  npx tsx lookup.ts kubernetes "deployment spec rolling update"
  npx tsx lookup.ts prisma "one-to-many relations"

Supported Libraries:
${Object.entries(COMMON_LIBRARIES)
  .map(([name]) => `  - ${name}`)
  .join("\n")}
  ...and 1000+ more at context7.com
`);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);

  if (args.length < 2 || args[0] === "--help" || args[0] === "-h") {
    printUsage();
    process.exit(args.length < 2 && args[0] !== "--help" && args[0] !== "-h" ? 1 : 0);
  }

  const libraryName = args[0];
  const query = args.slice(1).join(" ");

  try {
    const client = new Context7Client();

    // Check for known library ID to skip resolve step
    const knownId = getKnownLibraryId(libraryName);

    let libraryId: string;
    let libraryDisplayName = libraryName;

    if (knownId) {
      log("info", `Using known library ID for '${libraryName}': ${knownId}`);
      libraryId = knownId;
    } else {
      log("info", `Resolving library: ${libraryName}`);
      const searchResult = await client.resolveLibrary(libraryName, query);

      if (!searchResult.bestMatch) {
        log("error", `Library '${libraryName}' not found`);
        console.log("\nTip: Try one of these known libraries:");
        Object.keys(COMMON_LIBRARIES)
          .slice(0, 10)
          .forEach((name) => console.log(`  - ${name}`));
        process.exit(1);
      }

      libraryId = searchResult.bestMatch.id;
      libraryDisplayName = searchResult.bestMatch.name || libraryName;
      log("success", `Resolved to: ${libraryId}`);
    }

    // Query documentation
    const result = await client.queryDocs(libraryId, query);

    // Output formatted results
    console.log("\n" + "=".repeat(80));
    console.log(`📚 ${libraryDisplayName}`);
    console.log(`🔗 ${libraryId}`);
    console.log(`❓ ${query}`);
    console.log("=".repeat(80) + "\n");

    if (result.rawContent) {
      console.log(result.rawContent);
    } else if (result.snippets.length > 0) {
      result.snippets.forEach((snippet, index) => {
        console.log(`\n--- Snippet ${index + 1} ---`);
        if (snippet.title) console.log(`📄 ${snippet.title}\n`);
        console.log(snippet.content);
        if (snippet.url) console.log(`\n🔗 ${snippet.url}`);
      });
    } else {
      console.log("No documentation found for this query.");
      console.log("\nSuggestions:");
      console.log("  1. Try more specific terms (e.g., 'useEffect cleanup' instead of 'effects')");
      console.log("  2. Try broader terms (e.g., 'hooks' instead of 'useCustomHook')");
      console.log("  3. Include version if relevant (e.g., 'React 18 concurrent features')");
    }

    console.log("\n" + "=".repeat(80));
    log("success", "Documentation lookup complete");
  } catch (error) {
    log("error", error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

main();
