---
name: docs-create-local
description: Turn an external source — a product announcement, vendor blog post, release note, changelog entry, or docs URL — into self-contained documentation that lives in this repo, built from canonical vendor docs rather than the announcement's marketing copy and verified against the versions this repo actually pins. Use whenever someone points at a link and asks to "create documentation about this", "write local docs for", "document this feature", "make a local copy of these docs", "write this up for the team", or "add a doc about <new feature>". Also use when they name a docs tool (Context7, a docs MCP, Microsoft Learn, devdocs) alongside a URL, since that phrasing means they want a durable file in the repo, not a chat answer. Not for documenting code that already exists in the repo, and not for open-ended research with no file at the end.
---

# Create local documentation from an external source

Someone hands you a URL and asks for documentation. You already know to prefer canonical reference pages over the announcement's marketing copy, and to check claims before writing them down. This skill is about the three things that reliably get skipped anyway, and about what the finished file has to look like.

## What "local" means

Take the word literally: the reader has your file and nothing else.

- **Inline the tables.** If the billing model is a table on the vendor's page, that table is in your doc. "See pricing details" is a promise you failed to keep.
- **Complete the commands.** Exact CLI invocation, exact API version, exact argument name — not "configure it in the portal."
- **Links are provenance, not substitution.** Cite where each fact came from and when, so a future reader can judge staleness.

If you catch yourself writing "for more information, see…" as a way of not writing something, go get the information.

## The three checks that get skipped

Reading the reference page in full instead of trusting search snippets is table stakes; do it. These three are what separate a doc that holds up from one that reads well.

### Run the tool, and paste what it actually said

Vendor docs describe the tool as it was when the page was written. Run it and see. A docs page can label a command GA while the only extension shipping it is a beta build, or route you through a REST workaround that a newer CLI has replaced. `--help` output and `<tool> version` are cheap and dispositive.

**Paste the raw output verbatim into a fenced block. Never paraphrase it.** This matters more than it looks. Both configurations in this skill's own eval wrote confident sentences like "verified on this machine, `--help` reports `Allowed values: Cold, Cool, Hot, Premium, Smart`" for a CLI whose real output was `Allowed values: Cold, Cool, Hot, Premium.` — no `Smart`. The claim was shaped like verification and was invented, and it shipped to a repo.

Paraphrase is where fabrication hides, because a summary of output is indistinguishable from a plausible guess about output. Verbatim text with the command above it is checkable by the next reader in one paste. So: run the command, capture the output, paste it unedited, and if you find yourself writing a *description* of what a tool said rather than the text it said, you have not verified anything yet.

Before you finish, re-run every command in your provenance block and confirm the output still matches what you wrote.

**Do not install anything, and watch for tools that install themselves.** No `az extension add`, no `pip install`, no `brew install`. If a tool isn't present, that is a finding: record it as a gap rather than mutating the operator's machine to close it.

The trap is that refraining from typing an install command isn't sufficient. `az` dynamically installs an extension the first time you invoke an unknown command group, so a bare `az storage-actions --help` silently adds a package. A run in this skill's own eval mutated the machine exactly that way while intending not to. Before probing an unfamiliar command group, check whether it ships in core: `az extension list` first, and prefer `az extension list-available --query "[?name=='<group>']"` over invoking the group itself. If something does get installed, say so plainly in the doc rather than hoping nobody notices.

**Read enough context around a match.** When you grep tool output for a value, wrapped help text can push the thing you're looking for past your context window and invert your conclusion. This skill's own eval produced a false "the CLI rejects `Smart`" finding because `grep -A8` cut the allowed-values list one line short of `Smart`. Widen the window, or print the whole block, before concluding a value is absent. Absence of evidence in a truncated view is not evidence of absence.

### Get the real prices

Pricing pages are region-specific and client-rendered, so fetching one usually returns nothing usable. That is not a reason to omit prices — it is a reason to query the pricing API. For Azure:

```bash
curl -s -G "https://prices.azure.com/api/retail/prices" \
  --data-urlencode "api-version=2023-01-01-preview" \
  --data-urlencode "\$filter=serviceName eq 'Storage' and armRegionName eq 'brazilsouth' and contains(meterName, 'Smart')" \
  --data-urlencode "currencyCode=BRL"
```

Give a real rate in the reader's currency and region plus a worked example at realistic scale, or state plainly that you could not retrieve it and why. An invented number is worse than an admitted gap.

### Verify at the pin, not at latest

Docs and registries describe *latest*. Repos pin. A doc telling someone to set a value their pinned provider rejects is worse than no doc.

Find the pin (`versions.tf`, lockfile, `package.json`), then read the released artifact **at that version tag** — the vendored SDK enum, the schema definition, the constant. `curl` the raw file at the tag; it takes seconds. Two checks, not one: the enum existing only helps if the schema validates against it rather than a hand-written allowlist.

Prefer reading a specific file at a tag over asking a summarizer about a huge CHANGELOG — a large-document search that returns "no entries found" is inconclusive, not negative.

## Getting facts about this repo right

A doc full of correct vendor facts and wrong repo facts is embarrassing in a way the vendor half never is, because the reader can check the repo instantly.

The failure mode is checking the obvious location and stopping. A `just validate` recipe absent from the root `Justfile` may well be defined in `iac/justfile`. Search the whole tree for the thing before asserting it doesn't exist, and re-read your own doc for claims that contradict each other or contradict what the repo's existing docs say about its state.

Match the house style too: list the docs directory, read the index and one or two sibling docs, and follow what you find — header block, table density, diagram usage, language convention.

## Writing it

Start from `assets/doc-template.md` and adapt it to the house style you just read. Three sections that are easy to skip and shouldn't be:

- **Source discrepancies.** When two official pages disagree, document both and name the disagreement with your tiebreaker and reasoning. The feature's own reference page generally outranks a comparison page. A reader who hits the conflict in production and finds it already flagged trusts the rest of your doc.
- **Not covered / open questions.** What you couldn't verify and what it would take. This stops the doc from implying a completeness it doesn't have.
- **Provenance.** Sources with a retrieval date, plus the verification commands you ran and what they returned, so someone can re-run them against a newer pin.

```markdown
## Sources

Retrieved <YYYY-MM-DD>. Re-verify version-sensitive claims before acting on them.

| Source | Type | URL |
|---|---|---|

**Verified locally:**

`<the exact command>`

```
<the tool's raw output, pasted unedited — not a summary of it>
```

Confirms: <claim>. Re-verified <YYYY-MM-DD>.
```

Then wire it in: update the docs index, and run the repo's pre-commit guard if it has one — docs built from vendor pages sometimes carry example GUIDs or subscription IDs that trip secret scanners.

## Vendor recipes

- **Microsoft / Azure** — `references/microsoft.md`: the Learn MCP search-then-fetch pattern, where Azure feature facts actually live, and the pinned-version check for the AzureRM provider.
- **Libraries, SDKs, providers** — resolve through Context7, one concept per query. Context7 results usually reflect `main`, which is why the pin check exists.

## Anti-patterns

- Writing from the announcement alone. It has the date and the story, not the limitations list.
- A link farm. If half the doc is "see X for details", it isn't local.
- Quietly resolving a contradiction between two official sources.
