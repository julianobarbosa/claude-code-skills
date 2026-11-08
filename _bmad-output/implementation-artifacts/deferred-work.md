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
- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-detect-the-delivery-platform-with-ship-detect.md`
  summary: No CI job builds or tests the Rust crate (`cargo test`, `cargo clippy -D warnings`).
  evidence: `.github/workflows/` holds only `lint-skills.yml`; natural home is Story 1.3 (prebuilt binaries).
