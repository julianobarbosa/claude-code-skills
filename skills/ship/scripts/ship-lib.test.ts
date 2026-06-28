// Unit tests for the pure helpers in ship-lib.ts. Run: bun test (in the skill dir).
// These cover the parsing/derivation logic that has no side effects — git/network
// calls are intentionally out of scope here.

import { expect, test, describe } from "bun:test";
import {
  parsePorcelainStatus,
  scopeAudit,
  defaultTagsFromTitle,
  parseTags,
  parseWorkItem,
  detectKind,
  adoParts,
} from "./ship-lib.ts";

describe("parsePorcelainStatus", () => {
  test("empty tree", () => {
    expect(parsePorcelainStatus("")).toEqual({ staged: [], unstaged: [], untracked: [] });
  });

  test("staged only", () => {
    const s = parsePorcelainStatus("M  src/a.ts\nA  src/b.ts");
    expect(s.staged).toEqual(["src/a.ts", "src/b.ts"]);
    expect(s.unstaged).toEqual([]);
    expect(s.untracked).toEqual([]);
  });

  test("unstaged only", () => {
    const s = parsePorcelainStatus(" M src/a.ts");
    expect(s.staged).toEqual([]);
    expect(s.unstaged).toEqual(["src/a.ts"]);
  });

  test("untracked", () => {
    const s = parsePorcelainStatus("?? docs/index.md");
    expect(s.untracked).toEqual(["docs/index.md"]);
    expect(s.staged).toEqual([]);
    expect(s.unstaged).toEqual([]);
  });

  test("ignored entries are skipped", () => {
    const s = parsePorcelainStatus("!! node_modules/");
    expect(s).toEqual({ staged: [], unstaged: [], untracked: [] });
  });

  test("rename records the new path", () => {
    const s = parsePorcelainStatus("R  old.ts -> new.ts");
    expect(s.staged).toEqual(["new.ts"]);
  });

  test("modified in both index and worktree shows in both", () => {
    const s = parsePorcelainStatus("MM src/a.ts");
    expect(s.staged).toEqual(["src/a.ts"]);
    expect(s.unstaged).toEqual(["src/a.ts"]);
  });

  test("mixed tree", () => {
    const s = parsePorcelainStatus("M  staged.ts\n M unstaged.ts\n?? new.ts");
    expect(s.staged).toEqual(["staged.ts"]);
    expect(s.unstaged).toEqual(["unstaged.ts"]);
    expect(s.untracked).toEqual(["new.ts"]);
  });
});

describe("scopeAudit", () => {
  test("clean when only staged", () => {
    const a = scopeAudit("M  staged.ts");
    expect(a.ok).toBe(true);
    expect(a.warning).toBeUndefined();
  });

  test("clean on empty tree", () => {
    expect(scopeAudit("").ok).toBe(true);
  });

  test("not ok with unstaged, warning names the file", () => {
    const a = scopeAudit(" M docs/index.md");
    expect(a.ok).toBe(false);
    expect(a.warning).toContain("docs/index.md");
    expect(a.warning).toContain("not staged");
  });

  test("not ok with untracked, warning names the file", () => {
    const a = scopeAudit("?? new.ts");
    expect(a.ok).toBe(false);
    expect(a.warning).toContain("new.ts");
    expect(a.warning).toContain("untracked");
  });

  test("warning covers both unstaged and untracked", () => {
    const a = scopeAudit(" M a.ts\n?? b.ts");
    expect(a.ok).toBe(false);
    expect(a.warning).toContain("a.ts");
    expect(a.warning).toContain("b.ts");
  });
});

describe("defaultTagsFromTitle", () => {
  test("type + scope", () => {
    expect(defaultTagsFromTitle("docs(finops): OpenCost vs Infracost")).toEqual(["docs", "finops"]);
  });
  test("type only", () => {
    expect(defaultTagsFromTitle("fix: handle null token")).toEqual(["fix"]);
  });
  test("breaking-change bang is ignored for the tag", () => {
    expect(defaultTagsFromTitle("feat!: drop v1 API")).toEqual(["feat"]);
  });
  test("no conventional prefix falls back to needs-review", () => {
    expect(defaultTagsFromTitle("just some title")).toEqual(["needs-review"]);
  });
});

describe("parseTags", () => {
  test("splits CSV, trims, de-dupes, drops blanks", () => {
    expect(parseTags(["hotfix, do-not-merge", " hotfix ", ""])).toEqual(["hotfix", "do-not-merge"]);
  });
});

describe("parseWorkItem", () => {
  test("AB#1234", () => expect(parseWorkItem("AB#1234")).toBe("1234"));
  test("feature/837-foo", () => expect(parseWorkItem("feature/837-foo")).toBe("837"));
  test("no id", () => expect(parseWorkItem("main")).toBe(""));
});

describe("detectKind", () => {
  test("azure https", () => expect(detectKind("https://dev.azure.com/org/proj/_git/repo")).toBe("azure"));
  test("github ssh", () => expect(detectKind("git@github.com:user/repo.git")).toBe("github"));
  test("unknown", () => expect(detectKind("https://example.com/x.git")).toBe("unknown"));
});

describe("adoParts", () => {
  test("https dev.azure.com", () => {
    expect(adoParts("https://dev.azure.com/myorg/myproj/_git/myrepo")).toEqual({
      orgUrl: "https://dev.azure.com/myorg",
      project: "myproj",
      repo: "myrepo",
    });
  });
  test("non-azure url is null", () => {
    expect(adoParts("git@github.com:user/repo.git")).toBeNull();
  });
});
