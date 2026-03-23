# Setup — Main Vault Configuration Flow

Run from INSIDE the folder you want to become your Obsidian vault. Six steps: interview → infer → confirm → build → global context → verify.

## Step 1 — User Interview

Display this message exactly, then wait for their response:

---

**Tell me about yourself in a few sentences so I can build your vault.**

Answer these in whatever order feels natural:

- What do you do for work?
- What falls through the cracks most — what do you wish you tracked better?
- Work only, or personal life too?
- Do you have existing files to import? (PDFs, docs, slides)

No need to be formal. A few sentences is enough.

---

## Step 2 — Keyword-Driven Inference

From their free-text answer, detect keywords and infer vault structure. Do NOT ask clarifying questions — make smart inferences.

1. Read `RoleTemplates.md` for the keyword-to-folder mapping table
2. Scan the user's response for matching keywords
3. Base folders are always included: `inbox/`, `daily/`, `projects/`, `archive/`
4. Add folders for each keyword match (deduplicated)
5. Infer a role summary (1-2 sentences) from their description
6. Check `RoleTemplates.md` companion skill recommendations for their domain

Show the preview:

```
Here's your vault — ready to build when you are.

📁 [current directory name]
├── inbox/          Drop zone — everything new lands here first
├── daily/          Daily brain dumps and quick captures
├── [folder]/       [purpose from RoleTemplates.md]
├── [folder]/       [purpose from RoleTemplates.md]
├── projects/       Active work with status and next actions
└── archive/        Completed work — never deleted, just moved

CLAUDE.md will describe you as:
  [inferred role summary from their words]

Companion skills available:
  daily-skill   — start your day with vault context
  tldr-skill    — save session summaries to the right folder
  [domain-specific skills from RoleTemplates.md]

Recommended plugins: [top 4 from PluginRecommendations.md]

Type "build it" to create this, or tell me what to change.
```

Wait for confirmation before proceeding.

## Step 3 — Confirmation

Accept: "build it", "yes", "go", "looks good", or similar affirmative.

If they request changes, adjust the preview and show it again. Do NOT proceed until confirmed.

## Step 4 — Build

### Create folders

```bash
mkdir -p inbox daily [detected-role-folders] projects archive
```

### Open in Obsidian (cross-platform)

```bash
case "$(uname -s)" in
  Darwin)       open -a Obsidian "$(pwd)" ;;
  Linux)        xdg-open "obsidian://open?path=$(pwd)" ;;
  MINGW*|MSYS*) start "obsidian://open?path=$(pwd)" ;;
esac
```

### Write CLAUDE.md

Write directly to `CLAUDE.md` in the current directory. Use the user's actual words for the role description:

```markdown
# CLAUDE.md — [inferred role]'s Second Brain

## Who I Am
[2-3 sentences based on what they told you — specific, personal, written in
first person as Claude describing its owner]

## My Vault Structure
```
[folder tree with one-line purpose per folder]
```

## How I Work
[3-4 bullet points from RoleTemplates.md "How I Work" section, adapted to
match the user's specific description]

## Context Rules
[Context rules from RoleTemplates.md based on detected folders]
When something lands in inbox/ → ask if I want it sorted now
```

### Link companion skills

Instead of creating stub skill files, offer to symlink the real skills from the skills repo:

```bash
# Only if the user has claude-code-skills repo
SKILLS_REPO="$HOME/Repos/github/claude-code-skills/skills"

if [ -d "$SKILLS_REPO" ]; then
  mkdir -p .claude/skills
  ln -sf "$SKILLS_REPO/daily-skill" .claude/skills/daily-skill
  ln -sf "$SKILLS_REPO/tldr-skill" .claude/skills/tldr-skill
  echo "Linked daily-skill and tldr-skill from your skills repo."
else
  echo "Companion skills available at: https://github.com/[repo]/claude-code-skills"
  echo "Install them later with: ln -s /path/to/skills/daily-skill .claude/skills/daily-skill"
fi
```

**Do NOT create stub skill files.** Do NOT create a `memory.md` file — Claude Code's built-in memory system handles this.

## Step 5 — Safe Global Context Injection

Ask the user:

```
One last thing — how do you want your vault context loaded into Claude Code?

1. Global (recommended) — adds one line to ~/.claude/CLAUDE.md so your vault
   context loads automatically in every Claude Code session on this machine
2. Manual — I'll give you the line to paste into specific projects when you need it
3. Vault only — works automatically when you run claude from inside this folder
```

**If global (option 1):**

Idempotent injection — safe to run multiple times:

1. Check if `~/.claude/CLAUDE.md` exists
2. Search for vault path already referenced → skip if found ("Already configured")
3. Search for `## My Personal Context` section:
   - If found → append vault path line under it
   - If not found → append the section at end of file
4. If no file exists → create with just the section

The line to inject:
```
At the start of every session, read [absolute vault path]/CLAUDE.md for context about who I am, my work, and my conventions.
```

**If manual (option 2):** Show the line for them to paste.

**If vault only (option 3):** No action needed — skip.

Or use the CLI tool:
```bash
python Tools/VaultBuilder.py inject-global --vault-path "$(pwd)"
```

## Step 6 — Verification

Run `Workflows/Verify.md` to confirm everything was created correctly.

Then show:

```
Done. Your vault is live.

Your slash commands (if companion skills were linked):
  /daily    — run this tomorrow morning
  /tldr     — run this at the end of any session

Have files to import?
  See Workflows/ImportFiles.md or just drop files in inbox/ and say "sort my inbox"

Recommended plugins (install via Obsidian Settings → Community Plugins):
  [top 4 from PluginRecommendations.md for their role]
```
