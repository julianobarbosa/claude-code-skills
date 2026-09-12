// bun test ~/.claude/skills/ship-tag/Tools/ReleaseDocs.test.ts
import { describe, expect, test } from "bun:test";
import { consoleScripts, flattenNotes, renderDescription, renderReadme, requiresPython, type ReleaseInfo } from "./ReleaseDocs.ts";

const PY = `[build-system]
requires = ["hatchling"]

[project]
name = "widget"
version = "1.4.0"
requires-python = ">=3.10"

[project.scripts]
widget = "widget.cli:main"
widget-admin = "widget.admin:main"

[tool.hatch.build.targets.wheel]
packages = ["src/widget"]
`;
const NOTES = "### Added\n- Scheduled exports.\n\n### Fixed\n- Exports of large reports no longer time out.";
const INFO: ReleaseInfo = {
  pkg: "widget", version: "1.4.0", tag: "v1.4.0", commit: "9f3c2a1d4e5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d", date: "2026-09-11",
  orgUrl: "https://dev.azure.com/acme", feed: "tools", tarball: "widget-1.4.0.tar.gz",
  sha256: "4b2c7e1f0a9d8c6b5e4f3a2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b", notes: NOTES,
  compareUrl: "https://github.com/acme/widget/compare/v1.3.0...v1.4.0", scripts: ["widget", "widget-admin"],
  requiresPython: ">=3.10", repoBase: "https://github.com/acme/widget",
};

describe("pyproject parsing", () => {
  test("console scripts and requires-python", () => {
    expect(consoleScripts(PY)).toEqual(["widget", "widget-admin"]);
    expect(requiresPython(PY)).toBe(">=3.10");
    expect(consoleScripts("[project]\nname = \"x\"\n")).toEqual([]);
  });
});

describe("flattenNotes", () => {
  test("one sentence per change type", () => {
    expect(flattenNotes(NOTES)).toBe("Added: Scheduled exports. Fixed: Exports of large reports no longer time out.");
    expect(flattenNotes("")).toBe("");
  });
});

describe("renderDescription", () => {
  // Azure Artifacts rejects anything longer; a version can never be republished.
  const CAP = 256;
  test("what changed plus a short install command, inside the cap", () => {
    const d = renderDescription(INFO);
    expect(d.startsWith("widget 1.4.0 (2026-09-11). Added: Scheduled exports.")).toBe(true);
    expect(d).toContain("Install: az artifacts universal download --feed tools --name widget --version 1.4.0 --path . && uv pip install ./widget-1.4.0.tar.gz.");
    expect(d).toContain("Details: README.md in this package.");
    expect(d).not.toContain("--organization");
    expect(d.length).toBeLessThanOrEqual(CAP);
  });
  test("long notes are trimmed and the install line always survives", () => {
    const long = "### Added\n" + Array.from({ length: 80 }, (_, i) => `- Feature number ${i} with a fairly long description.`).join("\n");
    const d = renderDescription({ ...INFO, notes: long });
    expect(d.length).toBeLessThanOrEqual(CAP);
    expect(d).toContain("…");
    expect(d).toContain("uv pip install ./widget-1.4.0.tar.gz");
    expect(d).toContain("Details: README.md in this package.");
  });
  test("project-scoped feed adds --project and --scope", () => {
    expect(renderDescription({ ...INFO, feedProject: "Platform" })).toContain("--feed tools --project Platform --scope project --name widget");
  });
  test("when even the install line cannot fit, fall back to a pointer", () => {
    const d = renderDescription({ ...INFO, pkg: "a".repeat(120), tarball: `${"a".repeat(120)}-1.4.0.tar.gz` });
    expect(d.length).toBeLessThanOrEqual(CAP);
    expect(d).toContain("Install: see README.md in this package.");
  });
});

describe("renderReadme", () => {
  const r = renderReadme(INFO);
  test("install, verify, use and what changed", () => {
    expect(r).toContain("# widget 1.4.0");
    expect(r).toContain("az artifacts universal download --organization https://dev.azure.com/acme --feed tools --name widget --version 1.4.0 --path ./widget-1.4.0");
    expect(r).toContain('echo "4b2c7e1f0a9d8c6b5e4f3a2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b  widget-1.4.0.tar.gz" | sha256sum -c -');
    expect(r).toContain("uv pip install ./widget-1.4.0.tar.gz");
    expect(r).toContain("widget --help\nwidget-admin --help");
    expect(r).toContain("## What changed in 1.4.0\n\n### Added\n- Scheduled exports.");
    expect(r).toContain("Full diff: https://github.com/acme/widget/compare/v1.3.0...v1.4.0");
    expect(r).toContain("Python >=3.10");
  });
  test("no scripts and no notes still produce a usable README", () => {
    const bare = renderReadme({ ...INFO, scripts: [], notes: "", compareUrl: "" });
    expect(bare).toContain("importlib.metadata");
    expect(bare).toContain("_No CHANGELOG.md entries were found for this version._");
    expect(bare).not.toContain("Full diff:");
  });
});
