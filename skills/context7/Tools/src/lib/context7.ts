/**
 * Context7 API Client
 *
 * TypeScript client for Context7 documentation lookup API.
 * Provides up-to-date, version-specific documentation for libraries.
 *
 * @see https://context7.com/docs/api-guide
 */

const BASE_URL = "https://context7.com/api/v2";

export interface LibraryInfo {
  id: string;
  name: string;
  description?: string;
  codeSnippets?: number;
  reputation?: string;
  benchmarkScore?: number;
}

export interface SearchResult {
  libraries: LibraryInfo[];
  bestMatch: LibraryInfo | null;
}

export interface DocSnippet {
  title?: string;
  content: string;
  source?: string;
  url?: string;
}

export interface QueryResult {
  libraryId: string;
  query: string;
  snippets: DocSnippet[];
  rawContent: string;
}

export interface Context7Options {
  apiKey?: string;
  timeout?: number;
  /**
   * Max number of automatic retries on 429 Rate Limit responses
   * that include a `Retry-After` header. Default 1 (one retry, then fail).
   * Set to 0 to disable.
   */
  maxRetries?: number;
}

export type Context7ErrorKind =
  | "auth"
  | "not_found"
  | "rate_limit"
  | "server"
  | "timeout"
  | "other";

function kindFromStatus(status: number): Context7ErrorKind {
  if (status === 401 || status === 403) return "auth";
  if (status === 404) return "not_found";
  if (status === 429) return "rate_limit";
  if (status === 408) return "timeout";
  if (status >= 500 && status < 600) return "server";
  return "other";
}

function parseRetryAfter(headerValue: string | null): number | undefined {
  if (!headerValue) return undefined;
  const secs = Number(headerValue);
  if (Number.isFinite(secs) && secs >= 0) return secs;
  // HTTP-date form: convert to delta-seconds
  const ts = Date.parse(headerValue);
  if (Number.isFinite(ts)) {
    const delta = Math.max(0, Math.ceil((ts - Date.now()) / 1000));
    return delta;
  }
  return undefined;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Color codes for terminal output
 */
const Colors = {
  reset: "\x1b[0m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  cyan: "\x1b[36m",
  dim: "\x1b[2m",
} as const;

export type LogLevel = "silent" | "warn" | "info";

let currentLogLevel: LogLevel = "info";

export function setLogLevel(level: LogLevel): void {
  currentLogLevel = level;
}

export function getLogLevel(): LogLevel {
  return currentLogLevel;
}

export function log(level: "info" | "success" | "warn" | "error", message: string): void {
  // error always passes; warn passes unless silent; info/success only at level=info
  if (currentLogLevel === "silent" && level !== "error") return;
  if (currentLogLevel === "warn" && (level === "info" || level === "success")) return;

  const prefix = {
    info: `${Colors.blue}[INFO]${Colors.reset}`,
    success: `${Colors.green}[OK]${Colors.reset}`,
    warn: `${Colors.yellow}[WARN]${Colors.reset}`,
    error: `${Colors.red}[ERROR]${Colors.reset}`,
  };
  console.error(`${prefix[level]} ${message}`);
}

/**
 * Context7 API Client class
 */
export class Context7Client {
  private apiKey?: string;
  private timeout: number;
  private maxRetries: number;

  constructor(options: Context7Options = {}) {
    this.apiKey = options.apiKey || process.env.CONTEXT7_API_KEY;
    this.timeout = options.timeout || 30000;
    this.maxRetries = options.maxRetries ?? 1;
  }

  private buildHeaders(accept: string): Record<string, string> {
    const headers: Record<string, string> = { Accept: accept };
    if (this.apiKey) headers["Authorization"] = `Bearer ${this.apiKey}`;
    return headers;
  }

  private async doRequest(
    url: string,
    accept: string
  ): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);
    try {
      const response = await fetch(url, {
        method: "GET",
        headers: this.buildHeaders(accept),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === "AbortError") {
        throw new Context7Error("Request timed out", 408, undefined, "timeout");
      }
      throw new Context7Error(`Network error: ${error}`, 0, undefined, "other");
    }
  }

  /**
   * Drive doRequest with rate-limit retry. On 429 with Retry-After, sleeps
   * once and retries up to `maxRetries` times. Other non-2xx statuses surface
   * immediately as Context7Error with a typed `kind`.
   */
  private async doRequestWithRetry(url: string, accept: string): Promise<Response> {
    let attempt = 0;
    let lastRateLimitError: Context7Error | null = null;
    while (true) {
      const response = await this.doRequest(url, accept);
      if (response.ok) return response;

      const errorBody = await response.text().catch(() => "");
      const kind = kindFromStatus(response.status);
      const retryAfter = parseRetryAfter(response.headers.get("Retry-After"));

      const err = new Context7Error(
        `API request failed: ${response.status} ${response.statusText}`,
        response.status,
        errorBody,
        kind,
        retryAfter
      );

      if (kind === "rate_limit" && attempt < this.maxRetries && retryAfter !== undefined) {
        lastRateLimitError = err;
        log("warn", `Rate limited; retrying after ${retryAfter}s (attempt ${attempt + 1}/${this.maxRetries})`);
        await sleep(retryAfter * 1000);
        attempt++;
        continue;
      }

      // Exhausted retries or non-retryable status — throw the latest error.
      throw lastRateLimitError ?? err;
    }
  }

  private async fetch<T>(endpoint: string, params: Record<string, string>): Promise<T> {
    const url = new URL(`${BASE_URL}${endpoint}`);
    Object.entries(params).forEach(([key, value]) => {
      if (value) url.searchParams.set(key, value);
    });
    const response = await this.doRequestWithRetry(url.toString(), "application/json");
    return (await response.json()) as T;
  }

  /**
   * Fetch text/markdown content from API (for docs endpoint)
   */
  private async fetchText(endpoint: string, params: Record<string, string>): Promise<string> {
    const url = new URL(`${BASE_URL}${endpoint}`);
    Object.entries(params).forEach(([key, value]) => {
      if (value) url.searchParams.set(key, value);
    });
    const response = await this.doRequestWithRetry(url.toString(), "text/plain, text/markdown, */*");
    return await response.text();
  }

  /**
   * Resolve a library name to Context7 library ID
   */
  async resolveLibrary(libraryName: string, query?: string): Promise<SearchResult> {
    log("info", `Resolving library: ${libraryName}`);

    if (!this.apiKey) {
      log("warn", "No CONTEXT7_API_KEY set - using unauthenticated request (lower rate limits)");
    }

    const params: Record<string, string> = { libraryName };
    if (query) {
      params.query = query;
      log("info", `Using query context: ${query}`);
    }

    const data = await this.fetch<LibraryInfo[] | { results: LibraryInfo[] }>("/libs/search", params);

    // Handle different response formats
    const libraries = Array.isArray(data) ? data : data.results || [];

    if (libraries.length === 0) {
      log("warn", `No libraries found matching '${libraryName}'`);
      return { libraries: [], bestMatch: null };
    }

    log("success", `Found ${libraries.length} matching libraries`);

    return {
      libraries,
      bestMatch: libraries[0] || null,
    };
  }

  /**
   * Query documentation for a specific library
   * Note: The Context7 API returns plain markdown text, not JSON
   */
  async queryDocs(libraryId: string, query: string): Promise<QueryResult> {
    log("info", `Querying docs for: ${libraryId}`);
    log("info", `Query: ${query}`);

    if (!this.apiKey) {
      log("warn", "No CONTEXT7_API_KEY set - using unauthenticated request (lower rate limits)");
    }

    const rawContent = await this.fetchText("/context", { libraryId, query });

    if (!rawContent) {
      log("warn", "No documentation found for this query");
    } else {
      log("success", `Retrieved documentation (${rawContent.length} chars)`);
    }

    return {
      libraryId,
      query,
      snippets: [],
      rawContent,
    };
  }

  /**
   * Full lookup: resolve library and query docs in one call
   */
  async lookup(libraryName: string, query: string): Promise<QueryResult & { library: LibraryInfo | null }> {
    const searchResult = await this.resolveLibrary(libraryName, query);

    if (!searchResult.bestMatch) {
      throw new Context7Error(`Library '${libraryName}' not found`, 404, undefined, "not_found");
    }

    const libraryId = searchResult.bestMatch.id;
    const docsResult = await this.queryDocs(libraryId, query);

    return {
      ...docsResult,
      library: searchResult.bestMatch,
    };
  }
}

/**
 * Custom error class for Context7 API errors.
 *
 * `kind` is the user-facing category (mapped from HTTP status). `retryAfter` is
 * populated only on 429 responses that include a parseable `Retry-After` header.
 */
export class Context7Error extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public body?: string,
    public kind: Context7ErrorKind = "other",
    public retryAfter?: number
  ) {
    super(message);
    this.name = "Context7Error";
  }
}

/**
 * Common library ID mappings for quick reference
 */
export const COMMON_LIBRARIES: Record<string, string> = {
  react: "/facebook/react",
  "next.js": "/vercel/next.js",
  nextjs: "/vercel/next.js",
  vue: "/vuejs/vue",
  kubernetes: "/kubernetes/kubernetes",
  k8s: "/kubernetes/kubernetes",
  go: "/golang/go",
  golang: "/golang/go",
  python: "/python/cpython",
  node: "/nodejs/node",
  nodejs: "/nodejs/node",
  typescript: "/microsoft/typescript",
  ts: "/microsoft/typescript",
  angular: "/angular/angular",
  svelte: "/sveltejs/svelte",
  express: "/expressjs/express",
  fastify: "/fastify/fastify",
  nest: "/nestjs/nest",
  nestjs: "/nestjs/nest",
  prisma: "/prisma/prisma",
  drizzle: "/drizzle-team/drizzle-orm",
  tailwind: "/tailwindlabs/tailwindcss",
  tailwindcss: "/tailwindlabs/tailwindcss",
};

/**
 * Try to get a known library ID without API call
 */
export function getKnownLibraryId(libraryName: string): string | null {
  const normalized = libraryName.toLowerCase().trim();
  return COMMON_LIBRARIES[normalized] || null;
}

// Default client instance
let defaultClient: Context7Client | null = null;

export function getClient(options?: Context7Options): Context7Client {
  if (!defaultClient || options) {
    defaultClient = new Context7Client(options);
  }
  return defaultClient;
}
