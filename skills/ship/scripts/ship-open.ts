#!/usr/bin/env bun
// Open a URL (normally a just-created PR) in a browser, under a chosen account
// profile. The hard part isn't launching a browser — it's picking the *right*
// signed-in profile when you juggle several accounts. So this resolves an email
// to the browser's own profile directory by reading its `Local State` (the same
// map the browser's profile switcher shows), then launches that profile.
//
// No email or profile is baked in: the map is discovered live each run (it can
// change when you add/remove accounts), the email you want is an argument, and
// only your *default* email (+ browser) is remembered, in a file outside this skill.
//
// Works on WSL (-> Windows Edge/Chrome via cmd.exe start) and macOS (-> Chrome/Edge
// via `open`); native Linux is best-effort. Distinct from ship-tag.ts (PR labels)
// and ship-snapshot.ts (git tags) — this one just opens a browser window.
//
// Usage:
//   bun ship-open.ts <url> [--profile <email>] [--browser edge|chrome]
//   bun ship-open.ts --list-profiles [--browser edge|chrome]
//   bun ship-open.ts --set-default <email> [--browser edge|chrome]
//
//   <url>                     The page to open (required unless --list-profiles
//                             / --set-default). Normally the pr_url from ship-pr.ts.
//   --profile <email>         Open as this account. Falls back to the stored
//                             default, then to the browser's Default profile.
//   --browser edge|chrome     Force a browser. Default: the stored one, else
//                             whichever is installed (chrome preferred if both).
//   --list-profiles           Print the discovered email -> profile map and exit.
//                             Drives the "which account?" prompt in SKILL.md.
//   --set-default <email>     Remember this email (+ --browser) as the default and exit.
//   --dry-run                 Resolve + print the profile without launching a browser.
//   -h, --help                Show usage.
//
// Output (stdout, key=value): opened_url=  browser=  profile_dir=  profile_email=
//   --list-profiles instead prints: browser=  local_state=  and one
//   `profile=<dir>\t<email>\t<name>` line per profile.

import { execFileSync, spawn } from "node:child_process";
import { existsSync, readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join, dirname } from "node:path";
import { sh } from "./ship-lib.ts";

function fail(msg: string, code = 1): never {
  console.error(msg);
  process.exit(code);
}

type Browser = "edge" | "chrome";
type OS = "macos" | "wsl" | "linux";

// Per-browser, per-OS knobs: what `Local State` lives at and how to launch.
const BROWSERS: Record<Browser, {
  winExe: string;              // WSL: `cmd.exe start <winExe>`
  macApp: string;              // macOS: `open -a <macApp>`
  linuxBins: string[];         // native Linux binaries to try, in order
  localState: Record<OS, (home: string, winUser: string) => string>;
}> = {
  edge: {
    winExe: "msedge.exe",
    macApp: "Microsoft Edge",
    linuxBins: ["microsoft-edge", "microsoft-edge-stable"],
    localState: {
      wsl: (_h, u) => `/mnt/c/Users/${u}/AppData/Local/Microsoft/Edge/User Data/Local State`,
      macos: (h) => `${h}/Library/Application Support/Microsoft Edge/Local State`,
      linux: (h) => `${h}/.config/microsoft-edge/Local State`,
    },
  },
  chrome: {
    winExe: "chrome.exe",
    macApp: "Google Chrome",
    linuxBins: ["google-chrome", "google-chrome-stable", "chromium"],
    localState: {
      wsl: (_h, u) => `/mnt/c/Users/${u}/AppData/Local/Google/Chrome/User Data/Local State`,
      macos: (h) => `${h}/Library/Application Support/Google/Chrome/Local State`,
      linux: (h) => `${h}/.config/google-chrome/Local State`,
    },
  },
};

function detectOs(): OS {
  if (process.platform === "darwin") return "macos";
  if (process.env.WSL_DISTRO_NAME) return "wsl";
  try {
    if (readFileSync("/proc/version", "utf8").toLowerCase().includes("microsoft")) return "wsl";
  } catch { /* not readable — not WSL */ }
  if (existsSync("/mnt/c")) return "wsl";
  return "linux";
}

// The Windows username, needed to locate the Local State under /mnt/c on WSL.
// cmd.exe prints a harmless "UNC paths are not supported" note to stderr; the
// username lands on stdout, which is what sh() captures.
let _winUser = "";
function winUser(): string {
  if (!_winUser) _winUser = sh("cmd.exe", ["/c", "echo %USERNAME%"], { allowFail: true }).trim();
  if (!_winUser) fail("could not determine the Windows username (cmd.exe unavailable?)", 2);
  return _winUser;
}

function localStatePath(browser: Browser, os: OS): string {
  const home = homedir();
  return BROWSERS[browser].localState[os](home, os === "wsl" ? winUser() : "");
}

// ---- config (remembered default), outside the skill so nothing is baked in ----
interface OpenConfig { defaultProfileEmail?: string; browser?: Browser }
function configPath(): string {
  const base = process.env.XDG_CONFIG_HOME || join(homedir(), ".config");
  return join(base, "ship", "open.json");
}
function readConfig(): OpenConfig {
  const p = configPath();
  if (!existsSync(p)) return {};
  try { return JSON.parse(readFileSync(p, "utf8")); } catch { return {}; }
}
function writeConfig(cfg: OpenConfig): string {
  const p = configPath();
  mkdirSync(dirname(p), { recursive: true });
  writeFileSync(p, JSON.stringify(cfg, null, 2) + "\n");
  return p;
}

// ---- profile discovery ----
interface Profile { dir: string; email: string; name: string }
function loadProfiles(browser: Browser, os: OS): { path: string; profiles: Profile[] } {
  const path = localStatePath(browser, os);
  if (!existsSync(path)) fail(`no ${browser} profile data found (looked for ${path}). Is ${browser} installed?`, 2);
  let cache: Record<string, any> = {};
  try {
    cache = JSON.parse(readFileSync(path, "utf8"))?.profile?.info_cache ?? {};
  } catch (e) {
    fail(`could not parse ${browser} Local State (${path}): ${String(e)}`, 2);
  }
  const profiles = Object.entries(cache).map(([dir, v]) => ({
    dir,
    email: String(v?.user_name ?? ""),
    name: String(v?.name ?? dir),
  }));
  return { path, profiles };
}

// Which browser to use: explicit flag > stored default > whichever is installed
// (chrome preferred when both are). We probe by Local State existence.
function pickBrowser(os: OS, explicit: Browser | "", stored: Browser | undefined): Browser {
  if (explicit) return explicit;
  const installed = (["chrome", "edge"] as Browser[]).filter((b) => existsSync(localStatePath(b, os)));
  if (stored && installed.includes(stored)) return stored;
  if (installed.length) return installed[0];
  if (stored) return stored;
  fail("no supported browser (edge/chrome) found — pass --browser or install one", 2);
}

// ---- launch ----
function launch(os: OS, browser: Browser, profileDir: string, url: string): void {
  const meta = BROWSERS[browser];
  if (os === "wsl") {
    // `start` detaches and returns immediately. WSL interop quotes args with
    // spaces, so `--profile-directory=Profile 1` reaches Chrome/Edge intact.
    execFileSync("cmd.exe", ["/c", "start", meta.winExe, `--profile-directory=${profileDir}`, url], { stdio: "ignore" });
  } else if (os === "macos") {
    // -n new instance, -a app, --args forwards the rest to the browser.
    execFileSync("open", ["-na", meta.macApp, "--args", `--profile-directory=${profileDir}`, url], { stdio: "ignore" });
  } else {
    const bin = meta.linuxBins.find((b) => sh("bash", ["-lc", `command -v ${b}`], { allowFail: true }));
    if (!bin) fail(`no ${browser} binary found on PATH (tried ${meta.linuxBins.join(", ")})`, 2);
    // Detach so the browser outlives this script.
    spawn(bin, [`--profile-directory=${profileDir}`, url], { detached: true, stdio: "ignore" }).unref();
  }
}

// ---------------- arg parsing ----------------
let url = "";
let profileEmail = "";
let browserFlag: Browser | "" = "";
let listOnly = false;
let dryRun = false;
let setDefaultEmail: string | null = null;

const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  switch (a) {
    case "--profile": profileEmail = argv[++i]; break;
    case "--browser": {
      const b = argv[++i];
      if (b !== "edge" && b !== "chrome") fail(`--browser must be edge or chrome (got ${b})`, 2);
      browserFlag = b;
      break;
    }
    case "--list-profiles": listOnly = true; break;
    case "--dry-run": dryRun = true; break;
    case "--set-default": setDefaultEmail = argv[++i]; break;
    case "-h": case "--help":
      console.log(
        "Usage: bun ship-open.ts <url> [--profile <email>] [--browser edge|chrome] [--dry-run]\n" +
        "       bun ship-open.ts --list-profiles [--browser edge|chrome]\n" +
        "       bun ship-open.ts --set-default <email> [--browser edge|chrome]",
      );
      process.exit(0);
    default:
      if (a.startsWith("-")) fail(`unknown arg: ${a}`, 2);
      if (url) fail(`unexpected extra argument: ${a}`, 2);
      url = a;
  }
}

const os = detectOs();
const cfg = readConfig();

// --set-default: persist and exit.
if (setDefaultEmail !== null) {
  if (!setDefaultEmail) fail("--set-default needs an email", 2);
  const next: OpenConfig = { ...cfg, defaultProfileEmail: setDefaultEmail };
  if (browserFlag) next.browser = browserFlag;
  const p = writeConfig(next);
  console.error(`>> saved default profile ${setDefaultEmail}${next.browser ? ` (${next.browser})` : ""} to ${p}`);
  console.log(`default_profile_email=${setDefaultEmail}`);
  if (next.browser) console.log(`browser=${next.browser}`);
  process.exit(0);
}

const browser = pickBrowser(os, browserFlag, cfg.browser);
const { path: lsPath, profiles } = loadProfiles(browser, os);

// --list-profiles: print the map and exit (drives the SKILL.md prompt).
if (listOnly) {
  console.error(`>> ${browser} profiles from ${lsPath}`);
  console.log(`browser=${browser}`);
  console.log(`local_state=${lsPath}`);
  for (const p of profiles) console.log(`profile=${p.dir}\t${p.email || "(no account)"}\t${p.name}`);
  process.exit(0);
}

if (!url) fail("need a <url> to open (or use --list-profiles / --set-default)", 2);

// Resolve the requested email -> profile dir. Order: --profile, then stored
// default, then the browser's own Default profile. Never guess a wrong account.
const wanted = (profileEmail || cfg.defaultProfileEmail || "").trim();
let chosen: Profile | undefined;
if (wanted) {
  chosen = profiles.find((p) => p.email.toLowerCase() === wanted.toLowerCase());
  if (!chosen) {
    console.error(`>> no ${browser} profile signed in as ${wanted}; falling back to the Default profile`);
  } else if (!profileEmail) {
    console.error(`>> using stored default profile ${wanted}`);
  }
}
if (!chosen) {
  chosen = profiles.find((p) => p.dir === "Default") ?? profiles[0];
  if (!chosen) fail(`no ${browser} profiles found in ${lsPath}`, 2);
}

if (dryRun) {
  console.error(`>> dry run — would open ${browser} profile "${chosen.dir}"${chosen.email ? ` (${chosen.email})` : ""}`);
} else {
  console.error(`>> opening in ${browser} profile "${chosen.dir}"${chosen.email ? ` (${chosen.email})` : ""}`);
  launch(os, browser, chosen.dir, url);
}

console.log(`opened_url=${url}`);
console.log(`browser=${browser}`);
console.log(`profile_dir=${chosen.dir}`);
console.log(`profile_email=${chosen.email}`);
