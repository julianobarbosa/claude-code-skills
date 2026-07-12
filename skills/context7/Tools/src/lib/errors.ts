/**
 * Translate Context7Error kinds into structured CLI exit info.
 *
 * Exit code map (3..7 for typed Context7 errors, 1 for generic):
 *   3 auth        — 401, bad/missing API key
 *   4 not_found   — 404, library or doc path missing
 *   5 rate_limit  — 429, with optional retryAfter seconds
 *   6 server      — 5xx, transient server error
 *   7 timeout     — 408, request aborted by client timeout
 *   1 other       — unrecognized
 */

import { Context7Error } from "./context7.js";
import { ArgParseError } from "./flags.js";

export interface FormattedError {
  exitCode: number;
  message: string;
  hint?: string;
  retryAfter?: number;
}

export function formatError(err: unknown): FormattedError {
  if (err instanceof ArgParseError) {
    return { exitCode: err.exitCode, message: err.message };
  }

  if (err instanceof Context7Error) {
    switch (err.kind) {
      case "auth":
        return {
          exitCode: 3,
          message: err.message,
          hint: "Set CONTEXT7_API_KEY from context7.com/dashboard or pass --api-key",
        };
      case "not_found":
        return {
          exitCode: 4,
          message: err.message,
          hint: "Run resolve first or check the library ID format (/org/project)",
        };
      case "rate_limit":
        return {
          exitCode: 5,
          message: err.message,
          hint: err.retryAfter
            ? `Rate limited; retry in ${err.retryAfter}s or set CONTEXT7_API_KEY`
            : "Rate limited; retry shortly or set CONTEXT7_API_KEY",
          retryAfter: err.retryAfter,
        };
      case "server":
        return {
          exitCode: 6,
          message: err.message,
          hint: "Context7 server error — try again in a moment",
        };
      case "timeout":
        return {
          exitCode: 7,
          message: err.message,
          hint: "Request timed out; raise --timeout or check network",
        };
      default:
        return { exitCode: 1, message: err.message };
    }
  }

  if (err instanceof Error) {
    return { exitCode: 1, message: err.message };
  }
  return { exitCode: 1, message: String(err) };
}
