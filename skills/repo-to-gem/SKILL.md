---
name: repo-to-gem
description: Turn a GitHub repository, a docs subfolder of one, or a local directory into a ready-to-upload Google Gemini Gem pack - bundled knowledge files sized to the Gem limits, system instructions written from what the source actually says, and a setup sheet with test prompts. Use this whenever someone wants a Gem (or "custom Gemini", "Gemini expert", "Gemini assistant") that knows a repo, framework, tool, or documentation set - including "make a Gem from this repo", "turn these docs into a Gem", "create a Gem for <project>", "I want Gemini to answer questions about this codebase", or a GitHub URL pasted next to the word Gem. Also use it to refresh an existing Gem's knowledge after the repo changed. Not for NotebookLM notebooks (use notebooklm) and not for building a Claude skill from a repo.
---

# Repo to Gem

Build the three things a person needs to create a Gemini Gem that is an expert on one repository, so that they can upload and paste without editing anything.

## What you deliver

One folder, `gem-<slug>/` in the current directory unless the user names another place:

```
gem-<slug>/
├── knowledge/
│   └── <slug>-knowledge.txt        # or <slug>-knowledge.1.txt, .2.txt ... when split
├── gem-instructions.md             # paste into the Gem's Instructions box
└── gem-setup.md                    # name, description, upload list, test prompts, refresh command
```

The Gem needs a display name and a slug. Take the name from the user; if they gave none, build it from the repo plus the last path segment that says what the content is (`yamadashy/repomix` at `website/client/src/en/guide` -> "Repomix Guide"). `<slug>` is that name in kebab-case (`repomix-guide`).

## The limits you are packing for

These come from Google's help pages and drift over time, so re-check [Upload & analyze files in Gemini Apps](https://support.google.com/gemini/answer/14903178) when a number matters to the outcome.

| Limit | Value | Status |
|---|---|---|
| Knowledge files per Gem | 10 | reported limit |
| Size per file | 100 MB | from the help page |
| Model context window | 1M tokens | from the help page |
| Total knowledge you should aim for | about 500k tokens | heuristic, not a Google limit |

The 500k target is a working budget: the knowledge shares the context window with the instructions and the whole conversation, and a Gem that starts half full answers long threads badly. Go over it when the user has a reason, and say that you did.

Token counts come from repomix, which counts with an OpenAI tokenizer. Treat them as an estimate for Gemini, good to within a comfortable margin, not a measurement.

Write knowledge as `.txt`. Plain text is on every list of accepted Gem file types; `.md` and `.xml` are not reliably on them. The content inside can still be Markdown.

## Step 1: Pin down the source

Work out four things before running anything: the repository, the branch, the subpath (if any), and whether it is public.

A GitHub URL like `https://github.com/<org>/<repo>/tree/<branch>/<path>` carries all of the first three. Split it yourself:

- repository: `<org>/<repo>`
- branch: `<branch>`
- subpath: `<path>`

A local directory needs no splitting; you pack it in place.

**Stop and confirm before bundling anything that is not public.** Uploading knowledge to a Gem hands the content to Google and, if the Gem is shared, to everyone it is shared with. For a private, internal, or client repo, tell the user exactly which paths will be bundled and get a yes first. If you cannot tell whether a repo is public, ask.

## Step 2: Bundle the knowledge

Use repomix through `bunx`. It clones, filters, counts tokens, and scans for secrets in one pass.

Remote repo, whole thing:

```bash
bunx repomix --remote <org>/<repo> --remote-branch <branch> \
  --style markdown -o gem-<slug>/knowledge/<slug>-knowledge.txt
```

Remote repo, one subfolder:

```bash
bunx repomix --remote <org>/<repo> --remote-branch <branch> \
  --include "<path>/**" \
  --style markdown -o gem-<slug>/knowledge/<slug>-knowledge.txt
```

Local directory:

```bash
bunx repomix <dir> --style markdown -o gem-<slug>/knowledge/<slug>-knowledge.txt
```

**Never hand a `/tree/<branch>/<path>` URL to `--remote`.** Repomix accepts it without complaint and packs the entire repository. On a real run this turned a 26-file docs folder into 1,140 files and 1.4M tokens with no warning. The subpath only takes effect through `--include`.

Repomix creates the output folder itself. Read the `Pack Summary` block at the end of what it prints. Three lines matter:

- `Total Files` should be plausible for the scope you meant. A subfolder that reports a thousand files means the scope did not apply.
- `Total Tokens` is the number you check against the budget and record in the setup sheet.
- `Security` should report no suspicious files. Leave the scan on. If it flags something, exclude that file with `-i` and tell the user; do not ship it.

For a remote repo, record the commit you packed, because a branch name says nothing a month later:

```bash
git ls-remote https://github.com/<org>/<repo> <branch>
```

### When the bundle is too big

Shrink it in this order, re-running after each move, and stop as soon as it fits. The order goes from "removes noise" to "removes signal":

1. Narrow to what teaches: `--include "docs/**,README.md,**/*.md"` for a docs Gem. Most repos carry their whole explanation in a fraction of their files.
2. Drop what nobody asks a Gem about: `-i "**/*.test.*,**/tests/**,**/fixtures/**,**/*.snap,**/CHANGELOG*,**/i18n/**"`. Translated docs are a common silent multiplier; keep one language.
3. For source code the Gem must understand but not quote, add `--compress`, which keeps signatures and structure and drops bodies.
4. Only then accept a larger budget, with the user's say-so.

To find what is eating the budget, add `--token-count-tree 2000` to see every path above 2,000 tokens.

Lockfiles, `node_modules`, build output, and binaries are already excluded by repomix's defaults and the repo's `.gitignore`; you do not need to list them.

### When one file is not right

Splitting is about file count and file size, not tokens. A single `.txt` holds far more than the token budget allows before it nears 100 MB, so one file is the normal result. Split when the user wants knowledge they can swap piece by piece:

```bash
bunx repomix ... --split-output 2mb -o gem-<slug>/knowledge/<slug>-knowledge.txt
```

This writes `<slug>-knowledge.1.txt`, `<slug>-knowledge.2.txt`, and so on. Keep the count at 10 or below; raise the split size if it goes over.

A cleaner split for a repo with distinct areas is one repomix run per area, each with its own `--include` and its own output name (`<slug>-guides.txt`, `<slug>-reference.txt`). Named files let the Gem's instructions point at them.

## Step 3: Read what you bundled

Read the knowledge file before writing a word of instructions. The instructions are only as good as your reading, and a Gem told confident things that the docs do not say will repeat them to its users.

Pull out, in the source's own vocabulary:

- **What it is and who it is for.** One or two sentences.
- **The terms it defines.** Names of phases, roles, artifacts, commands, config keys.
- **How work flows.** The sequence a user follows, if the source describes one.
- **Exact formats.** File templates, CLI syntax, schemas the Gem will be asked to produce.
- **What it warns against.** Stated constraints, deprecated paths, version boundaries.

If a section of the template below has nothing behind it in the source, leave that section out. An empty methodology heading filled with plausible-sounding steps is the failure this step exists to prevent.

For a bundle too large to read whole, read the directory structure at the top of the file, then the README, overview, and getting-started pages, then search the rest for the terms those pages introduce.

## Step 4: Write the instructions

Write `gem-instructions.md`. Keep it to roughly one page: it is loaded on every turn, and detail belongs in the knowledge files where it costs nothing until it is needed. The instructions say who the Gem is, how to use the knowledge, and what shape answers take.

Fill this shape with what Step 3 found. Every `{{...}}` must be replaced or its section removed.

```markdown
# Role
You are an expert guide to {{TOPIC}}: {{ONE_SENTENCE_WHAT_IT_IS}}.
You help {{AUDIENCE}} {{WHAT_THEY_COME_TO_DO}}.

# Knowledge
Your knowledge files are a packed copy of {{SOURCE}} as of {{DATE}} ({{BRANCH_OR_COMMIT}}).
Each file entry starts with a `## File: <path>` header giving its path in the repository, and the Directory Structure section near the top lists every path.

- Answer from the knowledge files. Name the file path you drew from when it helps the user find more.
- When the knowledge files specify a format, command, or template, reproduce it exactly.
- When a question goes beyond the knowledge files, or concerns a version newer than {{DATE}}, say so plainly and then offer what general knowledge you have, labelled as such.

# Core concepts
{{TERMS_AND_ONE_LINE_DEFINITIONS}}

# How work flows
{{STAGES_IN_ORDER_WITH_WHAT_EACH_PRODUCES}}

# Output standards
{{ARTIFACT_FORMATS_OR_POINTERS_TO_THE_FILE_PATHS_THAT_DEFINE_THEM}}

# Things to get right
{{CONSTRAINTS_AND_COMMON_MISTAKES_THE_SOURCE_NAMES}}

# Style
Lead with the answer or the artifact. Be concise and technical. Use code blocks for anything the user will copy. Ask one clarifying question when the request could mean two different things in {{TOPIC}}.
```

The grounding rule tells the Gem to label general knowledge and carry on, not to refuse. A Gem that answers "not covered" to every adjacent question is one people stop opening.

## Step 5: Write the setup sheet

Write `gem-setup.md` so that someone who has never made a Gem can finish in two minutes.

```markdown
# {{GEM_NAME}} - Gem setup

## Create it
1. Open gemini.google.com, go to Gems, and choose New Gem.
2. Name: {{GEM_NAME}}
3. Description: {{ONE_LINE_DESCRIPTION}}
4. Instructions: paste the full contents of `gem-instructions.md`.
5. Knowledge: upload every file listed below.
6. Save, then run the test prompts.

## Knowledge files
| File | Size | Tokens (est.) | Contains |
|---|---|---|---|
| knowledge/{{FILE}} | {{SIZE}} | {{TOKENS}} | {{SCOPE}} |

Total: {{N}} of 10 files, about {{TOTAL_TOKENS}} tokens.

## Source
- Repository: {{REPO_URL}}
- Branch or commit: {{REF}}
- Scope: {{SUBPATH_OR_WHOLE_REPO}}
- Excluded: {{IGNORE_PATTERNS_OR_NONE}}
- Bundled on: {{DATE}}

## Test prompts
{{FIVE_PROMPTS}}

## Refresh
From {{FOLDER_THAT_CONTAINS_THE_GEM_FOLDER}}, run this, re-upload the knowledge files, and update the date in the instructions:

    {{EXACT_REPOMIX_COMMAND_USED}}
```

Make the five test prompts earn their place. Three should have answers you can point to in the knowledge (one definition, one how-to, one "produce this artifact"), one should need two parts of the docs combined, and one should fall outside the knowledge so the user can see the Gem say so. Beside each of the first four, put the path inside the repository where the answer lives (`guide/configuration.md`), not the name of the knowledge file.

The refresh command is the exact command you ran, flags and all, so the Gem can be kept current without rediscovering the scope. Its output path is relative, so say which folder to run it from. Write dates as `YYYY-MM-DD`.

## Step 6: Check the pack before handing it over

Run these and fix anything they turn up:

```bash
ls gem-<slug>/knowledge/ | wc -l                           # 10 or fewer
grep -c '{{' gem-<slug>/gem-instructions.md gem-<slug>/gem-setup.md   # 0 and 0
wc -c gem-<slug>/gem-instructions.md                       # about a page: a few thousand characters
```

Then tell the user: where the folder is, the file and token totals, what you excluded and why, and anything in the source you could not confirm. If the security scan flagged a file or you went past the token target, lead with that.
