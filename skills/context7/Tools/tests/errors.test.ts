import { describe, test, expect } from "bun:test";
import { Context7Error } from "../src/lib/context7.js";
import { ArgParseError } from "../src/lib/flags.js";
import { formatError } from "../src/lib/errors.js";

describe("formatError", () => {
  test("auth → exit 3 with API key hint", () => {
    const err = new Context7Error("Unauthorized", 401, undefined, "auth");
    const f = formatError(err);
    expect(f.exitCode).toBe(3);
    expect(f.hint).toContain("CONTEXT7_API_KEY");
  });

  test("not_found → exit 4 with resolve hint", () => {
    const err = new Context7Error("Not found", 404, undefined, "not_found");
    const f = formatError(err);
    expect(f.exitCode).toBe(4);
    expect(f.hint).toContain("/org/project");
  });

  test("rate_limit with retryAfter → exit 5, hint mentions seconds", () => {
    const err = new Context7Error("429", 429, undefined, "rate_limit", 30);
    const f = formatError(err);
    expect(f.exitCode).toBe(5);
    expect(f.retryAfter).toBe(30);
    expect(f.hint).toContain("30s");
  });

  test("rate_limit without retryAfter → exit 5, generic hint", () => {
    const err = new Context7Error("429", 429, undefined, "rate_limit");
    const f = formatError(err);
    expect(f.exitCode).toBe(5);
    expect(f.retryAfter).toBeUndefined();
    expect(f.hint).toContain("shortly");
  });

  test("server → exit 6", () => {
    const err = new Context7Error("Internal Server Error", 500, undefined, "server");
    const f = formatError(err);
    expect(f.exitCode).toBe(6);
    expect(f.hint).toContain("server error");
  });

  test("timeout → exit 7", () => {
    const err = new Context7Error("Request timed out", 408, undefined, "timeout");
    const f = formatError(err);
    expect(f.exitCode).toBe(7);
    expect(f.hint).toContain("--timeout");
  });

  test("other Context7Error → exit 1, no hint", () => {
    const err = new Context7Error("Weird error", 418, undefined, "other");
    const f = formatError(err);
    expect(f.exitCode).toBe(1);
    expect(f.hint).toBeUndefined();
  });

  test("ArgParseError → propagates its own exit code", () => {
    const err = new ArgParseError("Unknown flag: --bogus");
    const f = formatError(err);
    expect(f.exitCode).toBe(2);
    expect(f.message).toContain("--bogus");
  });

  test("plain Error → exit 1, just the message", () => {
    const f = formatError(new Error("boom"));
    expect(f.exitCode).toBe(1);
    expect(f.message).toBe("boom");
  });

  test("non-Error throwables → exit 1, stringified", () => {
    const f = formatError("a string was thrown");
    expect(f.exitCode).toBe(1);
    expect(f.message).toBe("a string was thrown");
  });
});
