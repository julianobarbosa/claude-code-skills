# Parity and startup speed of the `ship` binary

Story 5.1 evidence for cutover (Story 5.2). `examples/parity.rs` runs every subcommand through the TS
scripts (`bun scripts/ship-*.ts`) and the Rust binary side by side. It diffs their `key=value` stdout
lines and exit codes, and times median startup per subcommand. It exits non-zero on any difference or
speed miss.

## Run it

```sh
cd skills/ship
cargo build --release
cargo run --release --example parity -- \
  --github <github clone> --azure <azure clone> \
  [--github-pr <n>] [--azure-pr <id>] [--open-profile <email>] \
  [--runs 15] [--report <file>] [--live]
```

| Flag | Meaning |
|------|---------|
| `--github`, `--azure` | One clone per platform. Required. Only read, never written. |
| `--github-pr`, `--azure-pr` | Existing PR for the live `tag --list` read. Without it that case is `skipped`. |
| `--open-profile` | Adds `open <url> --dry-run --profile <email>`. Without it that case is `skipped`. |
| `--runs` | Timed runs per implementation and subcommand (default 15; one warm-up run is discarded). |
| `--report` | Writes the case and timing tables as markdown. Put it outside the source clones. |
| `--live` | Adds the write tier against the real remotes (below). |
| `--ship`, `--scripts` | Binary and TS directory (defaults `target/release/ship`, `scripts/`). |

Exit codes: `0` when every compared case is `same` and every timing row passes; `1` on any `DIFF`,
`ERROR`, timing `FAIL`, `LEFTOVER`, a changed source clone, a scratch directory left behind, or a
binary older than any file under `src/` (run `cargo build --release` first); `2` on a usage error (missing or
invalid clone, binary not built, bun not on `PATH`), checked before anything is created.

Only stdout lines matching `^[a-z_]+=` and the exit code are compared; stderr is human text. For
`tag … --list` the bare label-name lines after `platform=` are compared too. The values
of `pr_url`, `pr_id`, `pr_number` and `work_item` have each digit run replaced by `<N>` first, because
two live runs get different ids. On a `DIFF` both sides' lines are printed to the console (stdout), so use `--report`, not a shell
redirect, to get a file without stdout values. The report
holds case labels, verdicts, exit codes and timings, never stdout values, so Azure org, project and repo
names stay out of this public repo.

## How it stays safe

- For each platform and each implementation, the harness makes a scratch clone under the system temp dir
  (`git clone --no-local`, so nothing is hard-linked to the source). Origin keeps the real URL, so
  detection, Azure coordinate parsing and the Bearer branch behave as on a real clone.
  `url.<sink>.pushInsteadOf=<real url>` sends every push to a local bare repo instead. `git remote
  get-url` ignores `pushInsteadOf`, so both implementations still see the real URL. After building each
  scratch clone, the harness checks that its push URL is the sink and refuses to run any case if not.
- Each implementation has its own clone and sink, so one side's push or tag never changes what the other
  side sees. Both clones get the same setup (fixed author, committer and date), so `commit=` hashes match.
- The scratch root is created mode 0700. Scratch clones set `user.*`, turn off commit and tag signing
  (including `tag.forceSignAnnotated`), turn off `push.followTags`, use an empty `core.hooksPath` (also
  during the clone itself) and pin `status.showUntrackedFiles=normal`, so the usual global settings
  cannot change either side's result.
- Before and after the run, each source clone's `status`, branches, tags and local config are read with
  optional locks off. If anything changed, the run fails. The temp dir is removed at the end, and the run
  fails if it is still there.
- Every child is spawned from an argument array, with stdin closed, a hard timeout and
  `GIT_TERMINAL_PROMPT=0`. The branch nonce is letters only, so no work item can be inferred from it.

## Tiers

**Hermetic** (per platform; no network except the az token `push` mints on Azure):
`detect`; `detect` with `SHIP_PLATFORM` set to the other platform; `preflight` on a clean tree, after a
fixed-date commit plus one modified and one untracked file with a staged file added, after `push`, and
one commit ahead of upstream; `push`; `snapshot --name … -m …`; the same snapshot again (exit 3);
`snapshot --name … --push`; `push --bogus` and `snapshot --bogus` (exit 2); `pr` without `--title` and
`tag` without an id (exit 2). On Azure, when `az` can mint a token, `push` takes the Bearer branch
(`push_ok=oauth-bearer`, checked 2026-11-12) against the local sink.

**Live read:** `tag --list <id>` against the real API, when `--github-pr` or `--azure-pr` is given.

**Host-level:** `open --list-profiles`, `open <url> --dry-run`, and `--profile <email>` when given.
These read the real browser `Local State` and launch nothing.

**Timing:** `detect` and `preflight` run for real in the scratch clones. `push`, `pr`, `tag`, `snapshot`
and `open` would need the network for a real run, so `--help` is timed instead. For bun that measures
interpreter start plus module load, since imports are hoisted; for the binary it measures process start.
TS and Rust runs alternate. A row passes when the binary median is below the TS median and every run
exited 0. On Linux, `detect` and `preflight` binary medians must also be under 50 ms; elsewhere that rule
is skipped and the row says so.

**`--live`** (opt-in, writes to the real remotes): per platform, each implementation pushes its own
branch (`ship-parity-<nonce>-ts` / `-rs`) and opens a draft PR,
`pr --draft --title "chore: ship parity check (throwaway)" --no-create-work-item --no-reviewer`, so no
work item is created and no default reviewer is notified. It then runs
`tag <id> --add ship-parity`, `--remove ship-parity` and `--list` on its own PR. Cleanup is best-effort:
on GitHub, `gh pr close --delete-branch` plus deleting any `ship-parity`/`chore` label the run created;
on Azure, `az repos pr update --status abandoned` and `git push --delete`, Bearer first. Whatever could
not be cleaned is printed as `LEFTOVER`, and any leftover fails the run. Azure keeps tag definitions
project-wide. Not covered even by `--live`: work-item creation and linking, `--reviewer`, `--tag`,
`--related`, `--task` and the post-create `completionOptions` update. Those paths are covered by the Rust
tests against stub APIs and by Story 5.2's full ship run.

## Not compared

By the earlier stories' recorded decisions:

- A dirty tree whose first porcelain line is ` M <file>`. TS `sh()` trims the whole output, drops that
  leading space and counts the file as staged; the principal approved fixing this in Rust in Story 1.2
  (2026-11-08). The harness builds that tree but compares `preflight` only after adding a staged file that
  sorts first, which puts the bug out of play.
- A dash-prefixed positional remote such as `detect --bogus` (Story 1.1, finding 17).

## Latest recorded run

2026-11-12, agent run on Linux x86_64 (WSL2), bun 1.3.14 against ship 0.1.0, 15 timed runs, live tier
not run. Inputs: this repo (`--github-pr 35`), a one-commit Azure Repos clone, and `--open-profile` with
a signed-in profile on the host. Result: **PASS**, exit 0.

Cases: 32 same, 0 DIFF, 1 skipped (no `--azure-pr`), 0 ERROR. Source clones unchanged. Scratch
directory removed.

| Subcommand | Measured | TS median (ms) | RS median (ms) | Verdict |
|------------|----------|---------------:|---------------:|---------|
| detect | real run | 281.7 | 11.6 | pass (under 50 ms) |
| preflight | real run | 297.2 | 27.4 | pass (under 50 ms) |
| push | `--help` | 266.2 | 2.5 | pass |
| pr | `--help` | 286.9 | 2.6 | pass |
| tag | `--help` | 291.8 | 2.5 | pass |
| snapshot | `--help` | 266.4 | 2.5 | pass |
| open | `--help` | 271.1 | 2.6 | pass |

A negative check was also run: a stand-in binary that rewrites `scope_clean=true` to `false` on
`preflight` produced `DIFF` on both clean-tree cases and exit 1.

## Operator checklist before Story 5.2

The agent could not do these. Each needs a person, a login or another machine.

- [x] **Live Azure read.** The agent's `az` identity gets a 302 from the Azure DevOps org. Log in with an
  authorized account, then rerun with `--azure-pr <id>` and confirm `tag --list <id> (live read)` is `same`
  with exit 0 on both sides. Done 2026-11-13 on WSL2 with the company account: 33 same, 0 DIFF,
  0 skipped, 0 ERROR, exit 0; Azure and GitHub live reads both `same`.
- [x] **`--live` on both repos.** Run once with `--live` against the GitHub and the Azure clone. Confirm
  every `live …` case is `same` and no `LEFTOVER` lines are printed (or clean them up by hand).
  Done 2026-11-13 on WSL2: 43 same, 0 DIFF, 0 skipped, 0 ERROR, exit 0; all 10 `live …` cases `same`,
  0 leftovers, and no parity branch or open parity PR left on either remote.
- [ ] **macOS run.** Run the harness on macOS arm64. The 50 ms rule is skipped there, but the binary must
  still beat bun on every row.
- [x] **Confirm the 50 ms threshold.** It was adopted as a default on 2026-11-08 and confirmed by Barbosa
  on 2026-11-13; the binary measured about 12 ms (`detect`) and 28 ms (`preflight`) on WSL2.
- [ ] **Real `ship open` launches** (Epic 4 retro item 4). On WSL and on macOS, run
  `ship open <pr url> --profile <email>` without `--dry-run`. Confirm the PR opens in the browser profile
  signed in with that email.
