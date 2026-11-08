# Deferred Work

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-detect-the-delivery-platform-with-ship-detect.md`
  summary: A remote name starting with `-` is passed to `git remote get-url` as an option instead of a remote; use `--` before it.
  evidence: Edge-case and blind reviewers reproduced `ship detect -- -x` printing git usage and `url=`; `ship-detect.ts` behaves the same, so it is pre-existing.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-detect-the-delivery-platform-with-ship-detect.md`
  summary: Branch lookup via `rev-parse --abbrev-ref HEAD` prints `HEAD` on a detached head, fails on an unborn branch, and prints `heads/<name>` when a tag shares the branch name.
  evidence: Same command as TS `currentBranch()`; later push/PR stories consume `branch`, so fix it in both or at cutover.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-detect-the-delivery-platform-with-ship-detect.md`
  summary: Remote URL classification and Azure/GitHub parsing miss uppercase hosts, non-host substring matches, trailing slashes, `DefaultCollection`, `vs-ssh.visualstudio.com`, the project-less form, GitHub URLs with a port, and case variants of `SHIP_PLATFORM`.
  evidence: Edge-case reviewer verified each against the identical JS regexes in `ship-lib.ts`; pre-existing, changing them now would break parity.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-detect-the-delivery-platform-with-ship-detect.md`
  summary: Work-item inference finds false ids (`feature/tab12-fix` → 12, `AB#12345678` truncated to 1234567, date prefix `2026-11-08` → 2026).
  evidence: Verified on the JS regex in `parseWorkItem`; pre-existing. Pinning tests added in Story 1.1 lock today's behavior until it is fixed deliberately.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-audit-delivery-scope-with-ship-preflight.md`
  summary: Preflight's scope guard passes when `status.showUntrackedFiles=no` is configured (untracked files vanish) and counts a collapsed untracked directory as one file; pass `--untracked-files=all` (or `normal`) explicitly.
  evidence: Reproduced: `git -c status.showUntrackedFiles=no status --porcelain` prints nothing for an untracked file. Same command in `ship-preflight.ts`; high severity because it is the PR #192 miss the guard exists for. Candidate for the same treatment as the approved trim-bug fix.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-audit-delivery-scope-with-ship-preflight.md`
  summary: A failed `git status --porcelain` (corrupt index, I/O error) is read as an empty, clean tree and prints `scope_clean=true`.
  evidence: `unwrap_or_default()` mirrors TS `sh(..., { allowFail: true })`; the guard certifies a tree it never read.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-audit-delivery-scope-with-ship-preflight.md`
  summary: Porcelain v1 parsing keeps C-quoted paths (spaces, non-ASCII under `core.quotePath`), splits a quoted rename containing ` -> ` at the wrong arrow, and treats unmerged entries as generic staged+unstaged; switch to `status --porcelain -z`.
  evidence: Per `git-status(1)`; parser is a 1:1 port of `parsePorcelainStatus`.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-audit-delivery-scope-with-ship-preflight.md`
  summary: `commits_ahead_of_upstream` is 0 for a never-pushed branch with local commits, and counting `log --oneline` lines can be inflated by `log.showSignature`; use `rev-list --count` and report the no-upstream case distinctly.
  evidence: Same `git log --oneline @{u}..` as TS, whose comment promises the no-upstream case is "surfaced separately below" but never does it.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-2-save-a-checkpoint-with-ship-snapshot.md`
  summary: A `ship snapshot -m` paragraph that starts with `#` (e.g. `#123 fixed`) is silently dropped from the tag message by git's default `--cleanup=strip`; pass `--cleanup=whitespace` (or `verbatim`) to keep it.
  evidence: Reproduced on git 2.53: `-m '#123 fixed' -m keep` produced a body with only the subject and `keep`. Same `git tag -a -m` call in `ship-snapshot.ts`, so fixing it changes tag bodies versus TS and needs the principal's decision (like the Story 1.2 trim fix).
- source_spec: `_bmad-output/implementation-artifacts/spec-3-1-open-a-github-pr-with-labels-and-reviewers.md`
  summary: Default PR labels take any leading `Word:` in the title as a Conventional-Commit type, so `WIP: x` or `Re: y` creates and applies a `wip`/`re` label on the repo; restrict to a known type list before falling back to the branch prefix.
  evidence: Same regex as TS `defaultTagsFromTitle` (ship-lib.ts), so parity holds today; fixing it changes labels relative to TS and wants a deliberate decision.
