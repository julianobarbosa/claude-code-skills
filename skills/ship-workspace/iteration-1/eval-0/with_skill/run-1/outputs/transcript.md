# Open PR in browser under an explicitly-named profile

## Task
Open `https://github.com/julianobarbosa/.dotfiles/pull/31` in the browser as
`julianomb@gmail.com`. Eval constraint: pass `--dry-run` so no real window opens.

## Skill path taken
Ship SKILL.md § 4c ("Open the PR in the browser"). The relevant tool is
`scripts/ship-open.ts`, which resolves an **email → browser profile** by reading the
browser's own `Local State` account map, then launches that profile at the URL.

## Flags chosen
1. `--list-profiles` — discover the signed-in accounts and confirm the email is a real,
   attached account (not a guess).
2. `"<pr_url>" --profile julianomb@gmail.com --dry-run` — resolve the profile for the
   named email without opening a window (eval requirement).

I did **not** run `--set-default` — the user asked for a one-off open under a named
account, not to change their remembered default.

## Did I need to ask which profile?
No. The skill only prompts (via AskUserQuestion) when the account is ambiguous. Here the
email was named explicitly in the request, so resolution is deterministic — asking would
have been redundant. Three accounts exist (`juliano.barbosa@hypera.com.br` = Default,
`julianomb@gmail.com` = Profile 1, `juliano.b.cloud@hypera.com.br` = Profile 2); the named
email pinned exactly one.

## Resolved facts
- **Browser:** edge (WSL → Windows Edge; auto-detected, only Edge present)
- **Email:** julianomb@gmail.com
- **profile_dir:** Profile 1  (display name "julianomb@gmail.com")
- **URL surfaced / would-open:** https://github.com/julianobarbosa/.dotfiles/pull/31
- **Outcome:** dry run — would open edge profile "Profile 1" (julianomb@gmail.com); no
  window opened.

Note: the `UNC paths are not supported` lines on stderr are cosmetic — cmd.exe complaining
about the WSL working directory. The script still read the Edge `Local State` and resolved
the profile correctly.
