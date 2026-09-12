# Transcript — Old `ship` skill vs. "open the PR in the browser" (no account specified)

**Task (simulated user):** "open https://github.com/julianobarbosa/.dotfiles/pull/31 in the browser"
**Skill under test:** `ship` — `skill-snapshot` (genuine older version, no browser-open step, no `ship-open.ts`)
**Eval constraints:** don't actually open a browser, don't install packages, read-only discovery allowed, don't use any `ship-open.ts`.

---

## Did the old skill give ANY guidance about browser profiles or "which account"?

**No. None at all.** The old `ship` is a *delivery* skill: commit → push → open (create) a PR → ensure/link a Board work item → cleanup → optional git-tag snapshot. Every use of the word "open" in its SKILL.md means **create** a pull request via the API (Octokit / azure-devops-node-api), never "open a URL in a browser."

I verified this directly rather than assuming:

- `find` over the snapshot: six scripts — `ship-detect`, `ship-push`, `ship-pr`, `ship-tag`, `ship-snapshot`, `ship-lib`. **No `ship-open.ts`.**
- `grep -inE "browser|profile|xdg-open|--profile|edge|chrome"` against `SKILL.md` → **none**. Against `references/azure-devops.md` → **none**. (An earlier `grep -l` "hit" was only the substring "open" inside "open a PR.")

So there is zero coverage of: opening an existing PR URL, choosing a browser, browser profiles, or — the crux here — **resolving which account to use when the user names none.** The task falls entirely outside the skill's scope. The old skill's own description even lists browser-open as a trigger phrase in the *current* system prompt, but this snapshot's SKILL.md has no matching capability, so a model relying on the snapshot alone gets no help.

## What did I do about the ambiguity — discover, ask, or guess?

**I discovered the accounts myself, then flagged that I would ask, then proceeded on the best inference** (since I can't truly prompt in an eval). Concretely:

1. **Detected the environment.** `xdg-settings get default-web-browser` → no xdg-open. `/mnt/c/Users` exists → this is **WSL2**, so the real browser is the Windows browser, not a Linux one. The Linux `~/.config/google-chrome|microsoft-edge|chromium` dirs are empty stubs.
2. **Found the browser + profiles.** Windows Edge is installed (`msedge.exe` at the default path) with three profiles under `.../Edge/User Data`.
3. **Mapped profile → account** by parsing Edge's `Local State` `info_cache` (read-only):
   - `Default`   → **juliano.barbosa@hypera.com.br** (Hypera work)
   - `Profile 1` → **julianomb@gmail.com** (personal Gmail)
   - `Profile 2` → **juliano.b.cloud@hypera.com.br** (Hypera cloud)

That gave me the "which account" menu the skill never provided. Because the target is a **personal** repo (`github.com/julianobarbosa/.dotfiles`), the natural owner is the personal GitHub identity → **Profile 1 (julianomb@gmail.com)**. I state clearly that with no account specified I would normally ASK, and since I can't, I default to Profile 1 and name the alternatives.

## The command I would run (not executed)

```bash
"/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
  --profile-directory="Profile 1" \
  "https://github.com/julianobarbosa/.dotfiles/pull/31"
```

(Hypera work → `--profile-directory="Default"`; Hypera cloud → `--profile-directory="Profile 2"`.)

## How much did I have to improvise?

**Almost 100%.** The old skill contributed *nothing* to this task — no tool, no profile concept, no account-resolution guidance, no browser-launch mechanics. Everything that made the task solvable — recognizing WSL2, locating Windows Edge, enumerating profiles, mapping them to accounts, choosing `--profile-directory`, and reasoning about which account a personal-repo PR implies — I improvised from base tools and environment inspection. The skill's only tangential relevance is that it *creates* PRs; opening one in a chosen browser profile is a capability it simply does not have in this snapshot.
