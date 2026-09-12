# Transcript — open PR in Edge as work account (OLD ship skill)

**Task:** open `https://github.com/julianobarbosa/.dotfiles/pull/31` in Edge as the work account.
**Work account (from context):** `juliano.barbosa@hypera.com.br`
**Skill under test:** the genuine older `ship` snapshot — no browser-open step, no `ship-open.ts`.

## 1. Checking what the skill gives me

Read `skill-snapshot/SKILL.md` end to end. Its "Bundled tools" table lists exactly five
scripts: `ship-detect`, `ship-push`, `ship-pr`, `ship-tag`, `ship-snapshot`. Nothing about
opening a browser, nothing about Edge/Chrome profiles, no account→profile mapping. Confirmed on
disk — `scripts/` contains only those TS files, no `ship-open.ts`.

So the skill contributes **nothing** to this task. Everything below is hand work with base tools.

## 2. Finding Edge

No Edge on the Linux side (`which microsoft-edge/msedge` → nothing). This is WSL, so the real
browser is the Windows build. Found it at:

```
/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe
```

Edge's `--profile-directory` flag selects which profile to launch, but it takes the **on-disk
directory name** (`Default`, `Profile 1`, `Profile 2`, …), *not* the email. Edge deliberately
does not expose an "open as <email>" flag. So I have to translate the work email into whichever
directory Edge happens to have assigned it — and that assignment is arbitrary (first-signed-in
account lands in `Default`, not necessarily the one you'd guess).

## 3. Mapping the account to a profile directory — by hand

The only source of truth for the email→directory map is Edge's `Local State` file (a big JSON
blob) under the Windows user's `User Data`. There is no helper in this skill version, so I parsed
it manually.

- Located the Windows user: `/mnt/c/Users/juliano.barbosa/`.
- Located `.../AppData/Local/Microsoft/Edge/User Data/Local State` (59 KB).
- Listed the profile dirs actually present: `Default`, `Profile 1`, `Profile 2`.
- The mapping lives in `profile.info_cache` — an object keyed by directory name, each value
  holding `user_name` (the signed-in email), `gaia_name`, etc. I walked it with an inline
  `python3 -c` JSON one-liner (no jq dependency assumed, and the old skill offers no parser):

  | directory   | user_name                        | gaia_name                    |
  |-------------|----------------------------------|------------------------------|
  | `Default`   | `juliano.barbosa@hypera.com.br`  | Juliano Morais Barbosa       |
  | `Profile 1` | `julianomb@gmail.com`            | Juliano Barbosa              |
  | `Profile 2` | `juliano.b.cloud@hypera.com.br`  | Juliano Morais Barbosa Cloud |

**Disambiguation that mattered:** there are *two* `@hypera.com.br` accounts. The context pins the
work account as `juliano.barbosa@hypera.com.br`, which is the `Default` directory — not the
`juliano.b.cloud@...` one in `Profile 2`. Without the exact email from context, a naive guess
("hypera = work") would have been ambiguous. Manual parsing was the only way to be sure.

## 4. Result

Work account `juliano.barbosa@hypera.com.br` → Edge profile directory **`Default`**.

Command I would run (NOT executed — eval constraint forbids launching a browser):

```bash
"/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
  --profile-directory="Default" \
  "https://github.com/julianobarbosa/.dotfiles/pull/31"
```

## 5. Effort assessment

This was entirely manual. Six discovery steps: read SKILL.md, confirm no open script, locate the
Windows Edge binary, find the Windows user, find + stat `Local State`, then hand-parse its
`profile.info_cache` JSON and reason through the two-hypera-account collision. The old skill gave
zero assistance — no binary discovery, no profile resolution, no email→directory translation. A
dedicated helper (e.g. a `ship-open.ts` that reads `Local State` and matches on `user_name`) would
have collapsed all of section 3 into a single command.
