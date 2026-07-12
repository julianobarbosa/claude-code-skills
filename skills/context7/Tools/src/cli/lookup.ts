#!/usr/bin/env bun
/**
 * c7-lookup — Full documentation lookup (resolve + query in one command).
 *
 * Usage:
 *   c7-lookup <library_name> <query> [flags]
 *   bun src/cli/lookup.ts <library_name> <query> [flags]
 *
 * Examples:
 *   c7-lookup react "useEffect cleanup function"
 *   c7-lookup next.js "app router middleware" --json
 *   c7-lookup kubernetes "deployment spec fields" --no-cache --timeout 60000
 */

import {
  Context7Client,
  COMMON_LIBRARIES,
  getKnownLibraryId,
  log,
  setLogLevel,
} from "../lib/context7.js";
import { parseArgs, ArgParseError } from "../lib/flags.js";
import { formatError } from "../lib/errors.js";
import { getCached, setCached, clearCache } from "../lib/cache.js";
import pkg from "../../package.json" with { type: "json" };

const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours

function printUsage(): void {
  console.log(`
Usage: c7-lookup <library_name> <query> [flags]

Full documentation lookup — resolves library and queries docs in one command.

Arguments:
  library_name      Name of the library (e.g., "react", "next.js", "kubernetes")
  query             Natural language question about the library

Flags:
  --json            Emit JSON to stdout; suppress decorative output
  --quiet, -q       Suppress info/success logs (warn/error still on stderr)
  --no-cache        Bypass the resolve disk cache for this call
  --clear-cache     Remove the disk cache and exit
  --timeout <ms>    HTTP timeout in milliseconds (default 30000)
  --max-retries <n> Max retries on 429 Rate Limit (default 1)
  --api-key <key>   Override CONTEXT7_API_KEY env var
  --version, -V     Print version and exit
  --help, -h        This help

Environment:
  CONTEXT7_API_KEY  Optional API key for higher rate limits (context7.com/dashboard)

Examples:
  c7-lookup react "useEffect cleanup function"
  c7-lookup next.js "app router middleware" --json | jq .libraryId
  c7-lookup kubernetes "rolling update strategy" --timeout 60000

Known shortcuts (skip resolve, no API call):
${Object.keys(COMMON_LIBRARIES).map((name) => `  - ${name}`).join("\n")}
  ...plus 1000+ more libraries at context7.com
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
    if (positional.length < 2) process.exit(0);
  }

  if (positional.length < 2) {
    printUsage();
    process.exit(1);
  }

  if (flags.quiet || flags.json) setLogLevel(flags.json ? "warn" : "silent");

  const libraryName = positional[0]!;
  const query = positional.slice(1).join(" ");

  try {
    const client = new Context7Client({
      apiKey: flags.apiKey,
      timeout: flags.timeoutMs,
      maxRetries: flags.maxRetries,
    });

    let libraryId: string;
    let libraryDisplayName = libraryName;
    let source: "cache" | "known" | "resolved";

    const cached = flags.noCache ? null : await getCached(libraryName, CACHE_TTL_MS);
    const knownId = getKnownLibraryId(libraryName);

    if (cached) {
      libraryId = cached;
      source = "cache";
      log("info", `Cache hit for '${libraryName}': ${libraryId}`);
    } else if (knownId) {
      libraryId = knownId;
      source = "known";
      log("info", `Using known library ID for '${libraryName}': ${knownId}`);
    } else {
      log("info", `Resolving library: ${libraryName}`);
      const searchResult = await client.resolveLibrary(libraryName, query);
      if (!searchResult.bestMatch) {
        log("error", `Library '${libraryName}' not found`);
        if (!flags.json) {
          console.log("\nTip: Try one of these known libraries:");
          Object.keys(COMMON_LIBRARIES).slice(0, 10).forEach((name) => console.log(`  - ${name}`));
        }
        process.exit(4);
      }
      libraryId = searchResult.bestMatch.id;
      libraryDisplayName = searchResult.bestMatch.name || libraryName;
      source = "resolved";
      log("success", `Resolved to: ${libraryId}`);
      if (!flags.noCache) await setCached(libraryName, libraryId);
    }

    const result = await client.queryDocs(libraryId, query);

    if (flags.json) {
      const out = {
        library: libraryDisplayName,
        libraryId,
        query,
        source,
        rawContent: result.rawContent,
        snippets: result.snippets,
      };
      process.stdout.write(JSON.stringify(out, null, 2) + "\n");
    } else {
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
    }
  } catch (err) {
    const f = formatError(err);
    process.stderr.write(`Error: ${f.message}\n`);
    if (f.hint) process.stderr.write(`Hint: ${f.hint}\n`);
    process.exit(f.exitCode);
  }
}

main();
