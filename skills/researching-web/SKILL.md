---
name: researching-web
description: Search the web using Perplexity AI. Use when needing to search, look up, research, find current information, best practices, compare technologies, or answer factual questions about tools and libraries.
allowed-tools: Read, Grep, Glob, mcp__perplexity-ask__perplexity_ask
---

# Web Research with Perplexity

Use `mcp__perplexity-ask__perplexity_ask` for web search.

## When to Use

- Best practices and recommendations
- Current information (releases, news)
- Comparisons between technologies
- Factual questions about tools/libraries

## Usage

```json
{
  "messages": [{ "role": "user", "content": "Your research question" }]
}
```

## Tips

- Be specific: "Go error handling best practices 2024"
- Include context: "Redis vs Memcached for session storage"
- Ask comparisons: "Pros and cons of gRPC vs REST"

---

## Gotchas

- **Search quality varies by phrasing** — "X best practices" returns curated guides; "X mistakes" returns blog rants. Same intent, very different results.
- **Multi-source synthesis** doesn't auto-detect contradictions — facts from sources A and B may directly contradict; the skill doesn't flag this.
- **Date filtering ("last year") is unreliable** — search engines may include cached older content that was indexed recently.
- **Rate limits on the underlying search API silently truncate results** — a "no results" finding may actually be a quota issue.
- **Geo-targeting**: same query from different IPs returns different results — VPN switches mid-research produce inconsistent corpus.
- **NOT FOR official API/library reference** — for those use `looking-up-docs` (Context7); this skill is for trends, comparisons, news.
