# Transcript — Open PR #31 in browser (no profile specified)

**Task:** "open https://github.com/julianobarbosa/.dotfiles/pull/31 in the browser" — no account/profile specified.
**Skill:** `ship`, section **4c — Open the PR in the browser** (`scripts/ship-open.ts`).
**Eval constraint:** every browser-open command passed `--dry-run`; no real window opened.

---

## 1. Routing the request

The request maps cleanly to the ship skill's optional step 4c: "open the PR in my browser."
The skill is explicit that **which signed-in account you open the PR under matters** (work vs.
personal vs. cloud show different permissions / access), and that opening is **opt-in, never
automatic** — a browser window is a visible side effect, so the user should be prompted.

Because no profile was given, the skill's instruction is: *discover the accounts, then ask the
user which one with AskUserQuestion* — but only bother prompting when there is more than one
account.

## 2. Discovering the available accounts

Ran `bun scripts/ship-open.ts --list-profiles`. It read Edge's own `Local State` (the same account
map the browser's profile switcher shows) and returned **browser = edge** with three signed-in
accounts:

| Profile dir | Email | Display name | Likely use |
|-------------|-------|--------------|------------|
| `Default`   | `juliano.barbosa@hypera.com.br` | Perfil 1 | Work (Hypera) |
| `Profile 1` | `julianomb@gmail.com` | julianomb@gmail.com | Personal |
| `Profile 2` | `juliano.b.cloud@hypera.com.br` | juliano.b.cloud@hypera.com.br | Hypera cloud |

Three accounts ⇒ more than one ⇒ prompting **is** warranted per the skill.

## 3. Remembered default

Checked `~/.config/ship/open.json` (the skill stores only your *default* email there, outside the
skill dir). It exists and holds:

```json
{ "defaultProfileEmail": "julianomb@gmail.com", "browser": "edge" }
```

So a default **is** remembered: `julianomb@gmail.com` (personal) on Edge. This is also the sensible
match for the target — a personal `github.com/julianobarbosa/.dotfiles` repo. Per the skill, a
remembered default is offered "with one keypress," i.e. as the pre-selected option in the prompt.

## 4. The AskUserQuestion I would present

I would use **AskUserQuestion** here. (In this eval I cannot truly prompt, so I am listing the exact
options I would present and proceeding with the remembered default for the dry-run.)

- **Question:** "Which browser account should I open PR #31 under?"
- **Options:**
  1. **julianomb@gmail.com** — Personal (Edge "Profile 1"). *Remembered default — pre-selected.*
  2. **juliano.barbosa@hypera.com.br** — Work / Hypera (Edge "Default", Perfil 1).
  3. **juliano.b.cloud@hypera.com.br** — Hypera cloud (Edge "Profile 2").
  4. **Don't open** — just surface the PR URL, open nothing.

Yes — I mentioned the remembered default: option 1 is flagged as the stored default and would be
the pre-selected choice, so a single keypress accepts it.

## 5. Dry-run execution (default account)

Proceeding with the remembered default for the dry run:

```
bun scripts/ship-open.ts "https://github.com/julianobarbosa/.dotfiles/pull/31" \
  --profile julianomb@gmail.com --dry-run
```

Result (no window opened):

```
>> dry run — would open edge profile "Profile 1" (julianomb@gmail.com)
opened_url=https://github.com/julianobarbosa/.dotfiles/pull/31
browser=edge
profile_dir=Profile 1
profile_email=julianomb@gmail.com
```

## 6. PR URL surfaced

**https://github.com/julianobarbosa/.dotfiles/pull/31** — would open in Microsoft Edge under
profile "Profile 1" (`julianomb@gmail.com`). In a live (non-eval) run I would fire the same command
without `--dry-run` only after the user confirms the account via AskUserQuestion.
