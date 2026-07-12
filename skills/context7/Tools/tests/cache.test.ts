import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { existsSync, unlinkSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  readCache,
  writeCache,
  getCached,
  setCached,
  clearCache,
  getCachePath,
} from "../src/lib/cache.js";

const tmpPath = join(tmpdir(), `context7-cache-test-${process.pid}.json`);

beforeEach(() => {
  if (existsSync(tmpPath)) unlinkSync(tmpPath);
});

afterEach(() => {
  if (existsSync(tmpPath)) unlinkSync(tmpPath);
});

describe("cache", () => {
  test("readCache returns empty object when file missing", async () => {
    const entries = await readCache(tmpPath);
    expect(entries).toEqual({});
  });

  test("setCached then getCached roundtrip returns id", async () => {
    await setCached("React", "/facebook/react", tmpPath);
    const id = await getCached("react", 60_000, tmpPath);
    expect(id).toBe("/facebook/react");
  });

  test("name normalization is case-insensitive and trim-aware", async () => {
    await setCached("React", "/facebook/react", tmpPath);
    expect(await getCached("REACT", 60_000, tmpPath)).toBe("/facebook/react");
    expect(await getCached(" react ", 60_000, tmpPath)).toBe("/facebook/react");
  });

  test("getCached returns null when TTL exceeded", async () => {
    await setCached("foo", "/bar/baz", tmpPath);
    const entries = await readCache(tmpPath);
    entries["foo"]!.ts = Date.now() - 10_000;
    await writeCache(entries, tmpPath);

    const fresh = await getCached("foo", 1_000_000, tmpPath);
    expect(fresh).toBe("/bar/baz");

    const stale = await getCached("foo", 1_000, tmpPath);
    expect(stale).toBeNull();
  });

  test("clearCache removes the file", async () => {
    await setCached("x", "/y/z", tmpPath);
    expect(existsSync(tmpPath)).toBe(true);
    await clearCache(tmpPath);
    expect(existsSync(tmpPath)).toBe(false);
  });

  test("corrupt cache file is treated as empty", async () => {
    mkdirSync(join(tmpPath, ".."), { recursive: true });
    await Bun.write(tmpPath, "{ this is not json");
    const entries = await readCache(tmpPath);
    expect(entries).toEqual({});
  });

  test("getCachePath honors XDG_CACHE_HOME", () => {
    const old = process.env.XDG_CACHE_HOME;
    process.env.XDG_CACHE_HOME = "/tmp/xdg-test";
    try {
      expect(getCachePath()).toBe("/tmp/xdg-test/context7/resolved.json");
    } finally {
      if (old === undefined) delete process.env.XDG_CACHE_HOME;
      else process.env.XDG_CACHE_HOME = old;
    }
  });
});
