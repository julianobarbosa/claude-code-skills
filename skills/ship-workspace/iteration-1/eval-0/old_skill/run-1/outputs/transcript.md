# Transcript — "open PR #31 in my browser as julianomb@gmail.com" (OLD ship skill)

## The ask vs. what the skill gives me

The user pointed me at `https://github.com/julianobarbosa/.dotfiles/pull/31` and asked me to
open it in the browser signed in as **julianomb@gmail.com**.

I read the snapshot `SKILL.md` first. This version of `ship` is strictly a *delivery* skill:
commit → push → open PR (via SDK, not a browser) → link work item → snapshot. Its bundled
scripts are `ship-detect`, `ship-push`, `ship-pr`, `ship-tag`, `ship-snapshot`. There is:

- **no "open in browser" step** anywhere in the flow, and
- **no `ship-open.ts`** (I checked — `os error 2`, file does not exist).

The skill's description does list "open the PR in my browser / open it as <account>" as an
in-scope trigger, but the actual snapshot ships nothing that does it. So the skill triggers on
the request and then leaves me empty-handed. Everything below I had to improvise with base tools.

## Dead end #1: no browser on the Linux side

Natural first move: find a browser binary and just launch it. Nothing. `google-chrome`,
`chromium`, `microsoft-edge`, `brave`, `firefox`, `wslview` — none on PATH, and `$BROWSER` empty.

The `~/.config/{google-chrome,chromium,microsoft-edge,BraveSoftware}` dirs *exist*, which was a
brief false hope — but each contains only `NativeMessagingHosts`. No `Local State`, no `Default/`
profile, no `Profile N/`. They're empty scaffolding, not real installs. There is no Linux browser
here to map an account onto.

## Pivot: this is WSL2, the real browser is Windows-side

Since `/mnt/c` is mounted, the actual browser is a Windows app. `/mnt/c/Users` shows several
Windows accounts; `juliano.barbosa` is the one I can read (`drwxrwxrwx`). I probed the standard
Chromium-family user-data locations under `AppData/Local`:

- Chrome — absent
- Brave — absent
- Chromium — absent
- **Edge — present**, with a real `Local State` at
  `/mnt/c/Users/juliano.barbosa/AppData/Local/Microsoft/Edge/User Data/Local State`

So Edge is the only browser with profiles. No choice to make on browser — but I did have to
*discover* that rather than being told.

## The core manual work: mapping the email to a profile directory by hand

With no helper script, I parsed the browser's own internal registry myself. Chromium/Edge store
the account↔profile mapping in `Local State` under `profile.info_cache`: a JSON object keyed by
the on-disk **directory** name (`Default`, `Profile 1`, `Profile 2`), each value carrying
`user_name` (the signed-in email), `gaia_name`, and a display `name`.

`jq` happened to be installed, so I extracted the cache and read it off:

| dir on disk | signed-in email (`user_name`) | gaia_name |
|-------------|-------------------------------|-----------|
| `Default`   | juliano.barbosa@hypera.com.br | Juliano Morais Barbosa |
| **`Profile 1`** | **julianomb@gmail.com** | Juliano Barbosa |
| `Profile 2` | juliano.b.cloud@hypera.com.br | Juliano Morais Barbosa Cloud |

The match is unambiguous: **julianomb@gmail.com lives in the directory literally named
`Profile 1`.** The trap worth calling out — the display name of `Profile 1` also *happens* to be
the string "julianomb@gmail.com", but `--profile-directory` wants the **directory** name
(`Profile 1`), not the display name. Conflating the two would silently open the wrong (or a new)
profile. Resolving that distinction is precisely the job a dedicated helper would have done for me.

Had `jq` not been present I'd have fallen back to `bun`/`node` to `JSON.parse` the same file, or
grepped `"user_name"` out of it and eyeballed the surrounding keys — messier, but the same idea.

## Assembling the launch command

Edge executable confirmed at
`/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe` (the `(x86)` path is the real
one; the plain `Program Files` variant does not exist here). Chromium's account-scoped launch flag
is `--profile-directory="<dir>"`, with the URL as a trailing arg:

```
"/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
  --profile-directory="Profile 1" \
  "https://github.com/julianobarbosa/.dotfiles/pull/31"
```

Per the eval constraint I did **not** execute this — no browser window opened, nothing installed.
The command above is exactly what I would run.

## Guesswork / assumptions I had to make (couldn't ask the user)

- **Which Windows account.** I picked `juliano.barbosa` because it's the readable profile and
  matches the principal; the other `/mnt/c/Users` entries are permission-locked corp accounts.
- **Which browser.** Not a real decision in the end — Edge is the only one with profiles — but the
  request said "my browser" generically, and I inferred Edge from what actually exists on disk.
- **Reuse vs. fresh window.** If Edge is already running under another profile, `--profile-directory`
  opens the tab in the matching profile window; I assumed that's the desired behavior.

## Honest effort assessment

For what the user experiences as a one-liner ("open it as julianomb@gmail.com"), the old skill
forced roughly six discovery steps and a by-hand parse of a browser-internal JSON file: rule out
Linux browsers → realize it's WSL/Windows → find which browser has profiles → locate and parse
`Local State` → resolve the email-to-directory mapping (dodging the display-name-vs-directory-name
trap) → find the `.exe` → hand-assemble the flags. Every one of those is exactly the kind of thing
a dedicated `ship-open` helper would collapse into a single call. Without it, the task is doable
but entirely manual and fragile — it hinged on `jq` being available and on me knowing the
Chromium `Local State` / `--profile-directory` internals off the top of my head.
