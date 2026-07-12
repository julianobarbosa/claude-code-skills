/**
 * Context7 Tools - TypeScript client for documentation lookup
 *
 * @packageDocumentation
 */

export {
  Context7Client,
  Context7Error,
  type Context7Options,
  type Context7ErrorKind,
  type LibraryInfo,
  type SearchResult,
  type DocSnippet,
  type QueryResult,
  type LogLevel,
  getClient,
  getKnownLibraryId,
  COMMON_LIBRARIES,
  log,
  setLogLevel,
  getLogLevel,
} from "./lib/context7.js";

export {
  parseArgs,
  ArgParseError,
  type ParsedArgs,
  type ParsedFlags,
} from "./lib/flags.js";

export {
  formatError,
  type FormattedError,
} from "./lib/errors.js";

export {
  getCachePath,
  readCache,
  writeCache,
  getCached,
  setCached,
  clearCache,
  type CachedResolve,
} from "./lib/cache.js";
