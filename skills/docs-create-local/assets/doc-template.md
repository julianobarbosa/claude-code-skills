# <Feature or topic name>

> **Status:** <GA / preview / deprecated> since <date> · **Applies to:** <service / product scope>
> **Retrieved:** <YYYY-MM-DD> from official documentation — see [Sources](#sources)

<One paragraph, plain language: what this is and what problem it removes. Written for a colleague
who has never heard of it. No vendor adjectives.>

---

## How it works

<The mechanics, precisely. Thresholds, timers, what counts as a trigger and what doesn't.
This section is the reason the doc exists — an announcement will not give you this.>

<A table or a short mermaid diagram beats three paragraphs when the behavior is a state machine.>

## Prerequisites

| Requirement | Detail |
|---|---|
| <account/SKU/tier> | <exact value, and what is explicitly unsupported> |

## Enabling it

<Complete, runnable per-tool instructions. Include the exact API version, exact argument names.
Cover the tools this repo actually uses — don't pad with every SDK.>

```bash
<exact command>
```

**In this repo's IaC** *(only if applicable)*

```hcl
<exact config, at the provider version this repo pins>
```

## Cost model

<What is charged, what is free, and on what meter. Inline the vendor's table — do not link to it.
If rates are region-specific, say so and link the pricing page rather than inventing a number.>

| Cost category | Charged | Free |
|---|---|---|
| | | |

## Observing it

<Metrics, log fields, portal paths — the exact names, so someone can build a query or a dashboard
without going back to the vendor's site.>

## Limitations and gotchas

- <What's unsupported, what can't be undone, what silently conflicts with an existing mechanism>
- <Sovereign-cloud / regional differences>
- <One-way doors — configurations that can't be reversed>

## When to use this instead of <the alternative>

| If you need… | Use |
|---|---|
| | |

## Not covered / open questions

- <What you could not verify, and what it would take to verify it>

---

## Sources

Retrieved <YYYY-MM-DD>. Re-verify version-sensitive claims before acting on them.

| Source | Type | URL |
|---|---|---|
| <page title> | canonical reference | <url> |
| <page title> | comparison / positioning | <url> |
| <announcement title> | vendor announcement | <url> |

**Verified locally:**

- `<command run>` → `<result>` (confirms <claim>)

**Source discrepancies:**

- <Page A> states <value X>; <Page B> states <value Y>. <Which one is likelier authoritative and why.>
