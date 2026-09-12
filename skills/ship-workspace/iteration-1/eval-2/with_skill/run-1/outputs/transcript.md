# Open PR in Edge as work account — transcript

**Request:** "open the PR https://github.com/julianobarbosa/.dotfiles/pull/31 in edge as my work account"

**Eval constraint:** every browser-open command runs with `--dry-run`, so no real Edge window opens. Edge is forced with `--browser edge`.

## 1. Which part of `ship` applies

The URL is a GitHub PR, and nothing needs to be committed, pushed, or PR-opened — the PR already exists. This is purely SKILL.md **§4c "Open the PR in the browser"**, handled by `scripts/ship-open.ts`. That script's whole job is picking the *right signed-in profile* when several accounts share one browser, which is exactly what "as my work account" asks for.

## 2. Mapping "my work account" → an email

`ship-open.ts` does not take an account name — it takes an **email** (`--profile <email>`) and resolves it to the browser's profile directory. So "my work account" had to become a concrete email.

- The eval context (and the principal's identity / `userEmail`) gives the Hypera work address **`juliano.barbosa@hypera.com.br`**. That is the "work account."
- The personal Gmail (`julianomb@gmail.com`) and the secondary cloud address are explicitly *not* "work," so they were ruled out.

## 3. Discovering the email → profile map (live, not baked in)

`ship-open.ts` reads Edge's own `Local State` file — the same account map Edge's profile switcher shows — so the mapping is discovered fresh each run rather than hardcoded. Running `--list-profiles --browser edge` returned three signed-in Edge profiles:

| Edge profile dir | Signed-in email | Display name |
|------------------|-----------------|--------------|
| `Default` | **juliano.barbosa@hypera.com.br** | Perfil 1 |
| `Profile 1` | julianomb@gmail.com | julianomb@gmail.com |
| `Profile 2` | juliano.b.cloud@hypera.com.br | juliano.b.cloud@hypera.com.br |

Local State source: `/mnt/c/Users/juliano.barbosa/AppData/Local/Microsoft/Edge/User Data/Local State`.

The work email `juliano.barbosa@hypera.com.br` is the account signed into the **`Default`** profile. (A benign `cmd.exe` UNC-path warning prints because the script shells out to Windows from WSL to read Edge's Local State; it does not affect the result — exit code 0, map parsed correctly.)

## 4. Resolving + opening (dry-run)

With the email confirmed to exist in the map, I ran the open command forcing Edge and adding `--dry-run` so it resolves and prints the target profile without launching a window:

```
bun scripts/ship-open.ts "https://github.com/julianobarbosa/.dotfiles/pull/31" \
    --profile "juliano.barbosa@hypera.com.br" --browser edge --dry-run
```

Output:

```
>> dry run — would open edge profile "Default" (juliano.barbosa@hypera.com.br)
opened_url=https://github.com/julianobarbosa/.dotfiles/pull/31
browser=edge
profile_dir=Default
profile_email=juliano.barbosa@hypera.com.br
```

## 5. Resolved result

| Field | Value |
|-------|-------|
| Work account (email) | `juliano.barbosa@hypera.com.br` |
| Browser | `edge` (forced) |
| Resolved profile_dir | `Default` |
| URL surfaced | `https://github.com/julianobarbosa/.dotfiles/pull/31` |
| Window opened? | No — `--dry-run` (resolve-only, per eval constraint) |

The PR would open in Edge's `Default` profile — the Hypera work account — with no window actually launched.
