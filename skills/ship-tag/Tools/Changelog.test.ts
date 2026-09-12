// bun test ~/.claude/skills/ship-tag/Tools/Changelog.test.ts
import { describe, expect, test } from "bun:test";
import { INIT_TEMPLATE, addEntry, backfillLinks, fixText, lint, notesFor, parse, releaseChangelog, render, webFromRefs, yank } from "./Changelog.ts";

// The principal's sample, byte for byte: em dash separator, U+2011 in "auto-post".
const PRINCIPAL_SAMPLE = `# Changelog
All notable changes to this project are documented here.

## [Unreleased]
### Added
- Bulk export to CSV.

## [1.4.0] — 2026-07-05
### Added
- Slack integration: auto‑post on publish.
### Changed
- Dashboard loads 60% faster.
### Fixed
- SSL verification now completes within 60 seconds.
`;

// Keep a Changelog 1.1.0's own example, top three releases, verbatim (MIT, Olivier Lacan).
const KAC_EXAMPLE = `# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.2] - 2024-09-27

### Added
- v1.1 German translation
- v1.1 Italian translation

### Fixed
- Improve French translation
- Improve Dutch translation

## [1.1.1] - 2023-03-05

### Added
- Default to most recent versions available for each languages
- Centralize all links into \`/data/links.json\` for easy updates

### Fixed
- Missing periods at end of each change

### Changed
- Upgrade dependencies: Ruby 3.2.1, Middleman, etc.

### Removed
- Unused normalize.css file

## [1.1.0] - 2019-02-15

### Added
- Danish translation
- Georgian translation
- Changelog inconsistency section in Bad Practices

[unreleased]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.1.2...HEAD
[1.1.2]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.0.0...v1.1.0
`;

const GH = { kind: "github" as const, base: "https://github.com/acme/widget" };
const ADO = { kind: "azure" as const, base: "https://dev.azure.com/acme/Platform/_git/widget" };
const codes = (t: string) => lint(t).map((f) => `${f.level}:${f.code}`);

describe("parse/render", () => {
  test("round-trips the spec's example byte for byte", () => {
    expect(render(parse(KAC_EXAMPLE))).toBe(KAC_EXAMPLE);
  });
  test("round-trips the principal's sample byte for byte", () => {
    expect(render(parse(PRINCIPAL_SAMPLE))).toBe(PRINCIPAL_SAMPLE);
  });
});

describe("lint", () => {
  test("the spec's own example is clean", () => {
    expect(lint(KAC_EXAMPLE)).toEqual([]);
  });
  test("the init template is clean", () => {
    expect(lint(INIT_TEMPLATE)).toEqual([]);
  });
  test("the principal's sample: warnings only, the expected ones", () => {
    const c = codes(PRINCIPAL_SAMPLE);
    expect(c.filter((x) => x.startsWith("error"))).toEqual([]);
    expect(c).toContain("warning:W002"); // no SemVer statement
    expect(c).toContain("warning:W025"); // em dash separator
    expect(c).toContain("warning:W041"); // U+2011 in auto-post
    expect(c).toContain("warning:W050"); // [Unreleased] and [1.4.0] have no links
  });
  test("errors: bad date, unknown type, order, duplicates, stray heading", () => {
    const bad = `# Changelog

Uses Semantic Versioning.

## [Unreleased]

## [1.0.0] - 2024-13-01
### Improvements
- Something

## [1.2.0] - 2024-01-01
### Added
- A
### Added
- B

## [1.2.0] - 2024-01-02
### Fixed
- C

## Version 0.9 (old)
`;
    const c = codes(bad);
    expect(c).toContain("error:E024"); // month 13
    expect(c).toContain("error:E030"); // ### Improvements
    expect(c).toContain("error:E027"); // 1.2.0 below 1.0.0
    expect(c).toContain("error:E032"); // ### Added twice
    expect(c).toContain("error:E026"); // 1.2.0 twice
    expect(c).toContain("error:E020"); // unrecognized heading
  });
  test("commit-dump entries are flagged", () => {
    const t = INIT_TEMPLATE + "### Added\n- feat(api): add export\n- a1b2c3d fix typo\n- Merged PR 42: stuff\n";
    expect(codes(t).filter((x) => x === "warning:W040")).toHaveLength(3);
  });
  test("[Unreleased] must come first", () => {
    const t = INIT_TEMPLATE.replace("## [Unreleased]\n", "## [1.0.0] - 2024-01-01\n### Added\n- A\n\n## [Unreleased]\n");
    expect(codes(t)).toContain("error:E012");
  });
});

describe("fixText", () => {
  test("normalizes the separator and look-alike hyphens, then lint drops those warnings", () => {
    const r = fixText(PRINCIPAL_SAMPLE);
    expect(r.fixes).toBe(2);
    expect(r.text).toContain("## [1.4.0] - 2026-07-05");
    expect(r.text).toContain("auto-post");
    const c = codes(r.text);
    expect(c).not.toContain("warning:W025");
    expect(c).not.toContain("warning:W041");
  });
});

describe("addEntry", () => {
  test("appends to an existing group", () => {
    const r = addEntry(PRINCIPAL_SAMPLE, "added", "Scheduled exports.");
    expect(r.added).toBe(true);
    expect(notesFor(r.text, "Unreleased")).toBe("### Added\n- Bulk export to CSV.\n- Scheduled exports.");
  });
  test("creates a missing group in conventional order", () => {
    const once = addEntry(INIT_TEMPLATE, "Fixed", "Login no longer loops.").text;
    const twice = addEntry(once, "Added", "Dark mode.").text;
    expect(notesFor(twice, "Unreleased")).toBe("### Added\n- Dark mode.\n\n### Fixed\n- Login no longer loops.");
    expect(lint(twice)).toEqual([]);
  });
  test("is idempotent", () => {
    const r = addEntry(PRINCIPAL_SAMPLE, "Added", "- Bulk export to CSV.");
    expect(r.added).toBe(false);
    expect(r.text).toBe(PRINCIPAL_SAMPLE);
  });
  test("rejects unknown types", () => {
    expect(() => addEntry(INIT_TEMPLATE, "Improved", "x")).toThrow();
  });
});

describe("releaseChangelog", () => {
  const fixed = fixText(PRINCIPAL_SAMPLE).text;
  test("moves [Unreleased] into a dated version and writes GitHub links", () => {
    const t = releaseChangelog(fixed, "1.5.0", { date: "2026-09-11", web: GH });
    const d = parse(t);
    expect(d.sections.map((s) => s.heading)).toEqual(["## [Unreleased]", "## [1.5.0] - 2026-09-11", "## [1.4.0] - 2026-07-05"]);
    expect(notesFor(t, "1.5.0")).toBe("### Added\n- Bulk export to CSV.");
    expect(notesFor(t, "Unreleased")).toBe("");
    expect(t).toContain("[unreleased]: https://github.com/acme/widget/compare/v1.5.0...HEAD");
    expect(t).toContain("[1.5.0]: https://github.com/acme/widget/compare/v1.4.0...v1.5.0");
  });
  test("writes Azure DevOps branchCompare links", () => {
    const t = releaseChangelog(fixed, "1.5.0", { date: "2026-09-11", web: ADO, base: "main" });
    expect(t).toContain("[unreleased]: https://dev.azure.com/acme/Platform/_git/widget/branchCompare?baseVersion=GTv1.5.0&targetVersion=GBmain");
    expect(t).toContain("[1.5.0]: https://dev.azure.com/acme/Platform/_git/widget/branchCompare?baseVersion=GTv1.4.0&targetVersion=GTv1.5.0");
  });
  test("first release links to the tag", () => {
    const t = releaseChangelog(addEntry(INIT_TEMPLATE, "Added", "First cut.").text, "0.1.0", { date: "2026-01-02", web: GH });
    expect(t).toContain("[0.1.0]: https://github.com/acme/widget/releases/tag/v0.1.0");
    expect(lint(t)).toEqual([]);
  });
  test("drops empty groups when releasing", () => {
    const t = INIT_TEMPLATE + "### Added\n- X\n\n### Fixed\n\n### Security\n- Y\n";
    expect(notesFor(releaseChangelog(t, "1.0.0", { date: "2026-01-01" }), "1.0.0")).toBe("### Added\n- X\n\n### Security\n- Y");
  });
  test("refuses: empty [Unreleased], existing version, non-increasing version, bad date", () => {
    expect(() => releaseChangelog(INIT_TEMPLATE, "1.0.0", { date: "2026-01-01" })).toThrow("no entries");
    expect(() => releaseChangelog(fixed, "1.4.0", { date: "2026-01-01" })).toThrow("already");
    expect(() => releaseChangelog(fixed, "1.3.9", { date: "2026-01-01" })).toThrow("not greater");
    expect(() => releaseChangelog(fixed, "1.5.0", { date: "11/09/2026" })).toThrow("YYYY-MM-DD");
  });
  test("the released file lints clean once the preamble states SemVer", () => {
    const withSemver = fixed.replace("documented here.", "documented here.\nThis project adheres to Semantic Versioning.");
    const t = releaseChangelog(withSemver, "1.5.0", { date: "2026-09-11", web: GH });
    expect(codes(t)).toEqual(["warning:W050"]); // only [1.4.0] lacks a link: it predates the tool
  });
});

describe("yank and notes", () => {
  test("yank marks the heading and lint accepts it", () => {
    const r = yank(KAC_EXAMPLE, "1.1.1");
    expect(r.text).toContain("## [1.1.1] - 2023-03-05 [YANKED]");
    expect(lint(r.text)).toEqual([]);
    expect(yank(r.text, "1.1.1").changed).toBe(false);
  });
  test("notes returns one section's body", () => {
    expect(notesFor(KAC_EXAMPLE, "v1.1.0")).toBe("### Added\n- Danish translation\n- Georgian translation\n- Changelog inconsistency section in Bad Practices");
    expect(notesFor(KAC_EXAMPLE, "9.9.9")).toBe("");
  });
});

describe("iteration 2: layout, link inference, backfill", () => {
  test("add keeps a file's no-blank-line layout", () => {
    const t = addEntry(fixText(PRINCIPAL_SAMPLE).text, "Fixed", "Exports no longer time out.").text;
    expect(notesFor(t, "Unreleased")).toBe("### Added\n- Bulk export to CSV.\n### Fixed\n- Exports no longer time out.");
  });
  test("add keeps the spec's blank-line layout", () => {
    const t = addEntry(KAC_EXAMPLE, "Security", "Patched session fixation.").text;
    expect(t).toContain("## [Unreleased]\n\n### Security\n- Patched session fixation.\n\n## [1.1.2]");
  });
  test("release infers compare links from the file's existing references", () => {
    const t = releaseChangelog(addEntry(KAC_EXAMPLE, "Added", "Hindi translation").text, "1.2.0", { date: "2026-09-11" });
    expect(t).toContain("[1.2.0]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.1.2...v1.2.0");
    expect(t).toContain("[unreleased]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.2.0...HEAD");
  });
  test("webFromRefs reads GitHub and Azure DevOps bases", () => {
    expect(webFromRefs(parse(KAC_EXAMPLE).refs)).toEqual({ kind: "github", base: "https://github.com/olivierlacan/keep-a-changelog" });
    const ado = "[1.0.0]: https://dev.azure.com/acme/Platform/_git/widget?version=GTv1.0.0\n";
    expect(webFromRefs(parse(ado).refs)).toEqual({ kind: "azure", base: "https://dev.azure.com/acme/Platform/_git/widget" });
  });
  test("links backfills [Unreleased] and every version, clearing W050", () => {
    const r = backfillLinks(fixText(PRINCIPAL_SAMPLE).text, { web: GH });
    expect(r.added).toBe(2);
    expect(r.text).toContain("[unreleased]: https://github.com/acme/widget/compare/v1.4.0...HEAD");
    expect(r.text).toContain("[1.4.0]: https://github.com/acme/widget/releases/tag/v1.4.0");
    expect(codes(r.text)).not.toContain("warning:W050");
  });
  test("links adds nothing to a complete file; --rewrite fixes a wrong link but keeps the oldest", () => {
    expect(backfillLinks(KAC_EXAMPLE, {}).added).toBe(0);
    const broken = KAC_EXAMPLE.replace("compare/v1.1.0...v1.1.1", "compare/v1.0.0...v1.1.1");
    const r = backfillLinks(broken, { rewrite: true });
    expect(r.rewritten).toBe(1);
    expect(r.text).toBe(KAC_EXAMPLE);
  });
  test("links refuses when there is no URL anywhere", () => {
    expect(() => backfillLinks(fixText(PRINCIPAL_SAMPLE).text, {})).toThrow("no repository URL");
  });
});
