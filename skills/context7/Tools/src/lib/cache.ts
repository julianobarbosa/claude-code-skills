/**
 * Disk cache for resolved library IDs.
 *
 * Maps `libraryName` (lowercased) → `{ name, id, ts }`. TTL is checked at read time;
 * stale entries return null but remain on disk until overwritten by a fresh resolve
 * (cheap; deferred eviction). Corrupt JSON is treated as empty — the cache is
 * opportunistic, not authoritative.
 */

import { homedir } from "node:os";
import { join, dirname } from "node:path";
import { existsSync, mkdirSync, unlinkSync } from "node:fs";

export interface CachedResolve {
  name: string;
  id: string;
  ts: number;
}

export function getCachePath(): string {
  const xdg = process.env.XDG_CACHE_HOME;
  const root = xdg && xdg.trim() ? xdg : join(homedir(), ".cache");
  return join(root, "context7", "resolved.json");
}

function ensureCacheDir(path: string): void {
  const dir = dirname(path);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
}

export async function readCache(path: string = getCachePath()): Promise<Record<string, CachedResolve>> {
  const file = Bun.file(path);
  if (!(await file.exists())) return {};
  try {
    const data = await file.json();
    if (data && typeof data === "object" && !Array.isArray(data)) {
      return data as Record<string, CachedResolve>;
    }
    return {};
  } catch {
    return {};
  }
}

export async function writeCache(
  entries: Record<string, CachedResolve>,
  path: string = getCachePath()
): Promise<void> {
  ensureCacheDir(path);
  await Bun.write(path, JSON.stringify(entries, null, 2));
}

export async function getCached(
  name: string,
  ttlMs: number,
  path: string = getCachePath()
): Promise<string | null> {
  const cache = await readCache(path);
  const key = name.toLowerCase().trim();
  const entry = cache[key];
  if (!entry) return null;
  if (Date.now() - entry.ts > ttlMs) return null;
  return entry.id;
}

export async function setCached(
  name: string,
  id: string,
  path: string = getCachePath()
): Promise<void> {
  const cache = await readCache(path);
  const key = name.toLowerCase().trim();
  cache[key] = { name, id, ts: Date.now() };
  await writeCache(cache, path);
}

export async function clearCache(path: string = getCachePath()): Promise<void> {
  if (existsSync(path)) unlinkSync(path);
}
