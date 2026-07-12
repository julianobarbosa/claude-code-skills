/**
 * Shared CLI argument parser for c7-lookup, c7-resolve, c7-query.
 *
 * Throws `ArgParseError` on bad input so callers (and tests) can map to exit codes
 * without process.exit() hidden inside the parser.
 */

export interface ParsedFlags {
  help: boolean;
  version: boolean;
  json: boolean;
  quiet: boolean;
  noCache: boolean;
  clearCache: boolean;
  timeoutMs?: number;
  maxRetries?: number;
  apiKey?: string;
}

export interface ParsedArgs {
  positional: string[];
  flags: ParsedFlags;
}

export class ArgParseError extends Error {
  constructor(message: string, public exitCode: number = 2) {
    super(message);
    this.name = "ArgParseError";
  }
}

const KNOWN_FLAGS = new Set<string>([
  "--help", "-h",
  "--version", "-V",
  "--json",
  "--quiet", "-q",
  "--no-cache",
  "--clear-cache",
  "--timeout",
  "--max-retries",
  "--api-key",
]);

function takeValue(argv: string[], i: number, flag: string): string {
  const v = argv[i + 1];
  if (v === undefined || v.startsWith("-")) {
    throw new ArgParseError(`${flag} requires a value`);
  }
  return v;
}

function parsePositiveNumber(raw: string, flag: string): number {
  const n = Number(raw);
  if (!Number.isFinite(n) || n <= 0) {
    throw new ArgParseError(`${flag} must be a positive number, got: ${raw}`);
  }
  return n;
}

function parseNonNegativeInt(raw: string, flag: string): number {
  const n = Number(raw);
  if (!Number.isInteger(n) || n < 0) {
    throw new ArgParseError(`${flag} must be a non-negative integer, got: ${raw}`);
  }
  return n;
}

export function parseArgs(argv: string[]): ParsedArgs {
  const positional: string[] = [];
  const flags: ParsedFlags = {
    help: false,
    version: false,
    json: false,
    quiet: false,
    noCache: false,
    clearCache: false,
  };

  let i = 0;
  while (i < argv.length) {
    const arg = argv[i];
    if (arg === undefined) { i++; continue; }

    const looksLikeFlag = arg.startsWith("--") || (arg.startsWith("-") && arg.length === 2);

    if (looksLikeFlag) {
      if (!KNOWN_FLAGS.has(arg)) {
        throw new ArgParseError(`Unknown flag: ${arg}`);
      }
      switch (arg) {
        case "--help":
        case "-h":
          flags.help = true; break;
        case "--version":
        case "-V":
          flags.version = true; break;
        case "--json":
          flags.json = true; break;
        case "--quiet":
        case "-q":
          flags.quiet = true; break;
        case "--no-cache":
          flags.noCache = true; break;
        case "--clear-cache":
          flags.clearCache = true; break;
        case "--timeout":
          flags.timeoutMs = parsePositiveNumber(takeValue(argv, i, "--timeout"), "--timeout");
          i++;
          break;
        case "--max-retries":
          flags.maxRetries = parseNonNegativeInt(takeValue(argv, i, "--max-retries"), "--max-retries");
          i++;
          break;
        case "--api-key":
          flags.apiKey = takeValue(argv, i, "--api-key");
          i++;
          break;
      }
    } else {
      positional.push(arg);
    }
    i++;
  }

  return { positional, flags };
}
