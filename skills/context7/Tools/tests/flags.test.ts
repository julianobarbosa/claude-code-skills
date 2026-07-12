import { describe, test, expect } from "bun:test";
import { parseArgs, ArgParseError } from "../src/lib/flags.js";

describe("parseArgs", () => {
  test("positional only", () => {
    const r = parseArgs(["react", "useEffect cleanup"]);
    expect(r.positional).toEqual(["react", "useEffect cleanup"]);
    expect(r.flags.json).toBe(false);
    expect(r.flags.help).toBe(false);
  });

  test("interleaved flag and positional", () => {
    const a = parseArgs(["react", "--json", "useEffect"]);
    const b = parseArgs(["--json", "react", "useEffect"]);
    const c = parseArgs(["react", "useEffect", "--json"]);
    expect(a.flags.json).toBe(true);
    expect(b.flags.json).toBe(true);
    expect(c.flags.json).toBe(true);
    expect(a.positional).toEqual(["react", "useEffect"]);
    expect(b.positional).toEqual(["react", "useEffect"]);
    expect(c.positional).toEqual(["react", "useEffect"]);
  });

  test("--timeout parses a positive number", () => {
    const r = parseArgs(["--timeout", "10000", "react"]);
    expect(r.flags.timeoutMs).toBe(10000);
    expect(r.positional).toEqual(["react"]);
  });

  test("--timeout rejects non-positive", () => {
    expect(() => parseArgs(["--timeout", "0"])).toThrow(ArgParseError);
    expect(() => parseArgs(["--timeout", "-5"])).toThrow(ArgParseError);
    expect(() => parseArgs(["--timeout", "abc"])).toThrow(ArgParseError);
  });

  test("--max-retries parses non-negative integer", () => {
    expect(parseArgs(["--max-retries", "0"]).flags.maxRetries).toBe(0);
    expect(parseArgs(["--max-retries", "3"]).flags.maxRetries).toBe(3);
    expect(() => parseArgs(["--max-retries", "1.5"])).toThrow(ArgParseError);
    expect(() => parseArgs(["--max-retries", "-1"])).toThrow(ArgParseError);
  });

  test("--api-key takes a value", () => {
    const r = parseArgs(["--api-key", "ctx7sk_xxx", "react"]);
    expect(r.flags.apiKey).toBe("ctx7sk_xxx");
    expect(r.positional).toEqual(["react"]);
  });

  test("flag value missing throws", () => {
    expect(() => parseArgs(["--timeout"])).toThrow(ArgParseError);
    expect(() => parseArgs(["--api-key"])).toThrow(ArgParseError);
  });

  test("unknown flag throws with exit code 2", () => {
    try {
      parseArgs(["--bogus"]);
      throw new Error("should have thrown");
    } catch (e) {
      expect(e).toBeInstanceOf(ArgParseError);
      expect((e as ArgParseError).exitCode).toBe(2);
      expect((e as ArgParseError).message).toContain("--bogus");
    }
  });

  test("--help and -h short-circuit (parse to flag, not positional)", () => {
    expect(parseArgs(["--help"]).flags.help).toBe(true);
    expect(parseArgs(["-h"]).flags.help).toBe(true);
    expect(parseArgs(["react", "--help"]).flags.help).toBe(true);
  });

  test("--version and -V parse", () => {
    expect(parseArgs(["--version"]).flags.version).toBe(true);
    expect(parseArgs(["-V"]).flags.version).toBe(true);
  });

  test("--quiet and --no-cache and --clear-cache parse", () => {
    const r = parseArgs(["--quiet", "--no-cache", "--clear-cache"]);
    expect(r.flags.quiet).toBe(true);
    expect(r.flags.noCache).toBe(true);
    expect(r.flags.clearCache).toBe(true);
  });
});
