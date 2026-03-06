---
name: YouTubeSearch
description: Search YouTube and return structured video results with metadata and engagement metrics using yt-dlp. USE WHEN youtube search, find videos, search videos, video research, youtube results, channel research, video metrics, trending videos, content research. Even if the user just says "search YouTube for X" or "find videos about X", use this skill.
---

# YouTubeSearch

Search YouTube by query and return structured, human-readable results with metadata and engagement metrics.

## What It Does

Runs a yt-dlp search against YouTube, returning the top N results (default 20) filtered to a recent time window (default 6 months). Each result includes:

- **Title** and **URL**
- **Channel name** and **subscriber count**
- **View count** and **duration**
- **Upload date**
- **Engagement ratio** (views / subscribers) — a quick signal for whether a video over- or under-performed relative to the channel's audience

Numbers are human-readable (e.g., 1.2M, 45.3K). Results are separated by dividers for easy scanning.

## Requirements

- `yt-dlp` installed and in PATH
- `jq` installed and in PATH
- `bc` installed (standard on macOS/Linux)

## Usage

Run the bundled script:

```bash
bash ~/.claude/skills/YouTubeSearch/scripts/yt-search.sh "<search query>" [--count N] [--months N]
```

### Parameters

| Flag | Default | Description |
|------|---------|-------------|
| (positional) | — | Search query (required) |
| `--count` | 20 | Number of results to return |
| `--months` | 6 | Only include videos from the last N months |

### Examples

```bash
# Basic search — top 20 results from last 6 months
bash ~/.claude/skills/YouTubeSearch/scripts/yt-search.sh "kubernetes security best practices"

# Narrow to 5 results from the last month
bash ~/.claude/skills/YouTubeSearch/scripts/yt-search.sh "rust async tutorial" --count 5 --months 1

# Broader window — last 2 years
bash ~/.claude/skills/YouTubeSearch/scripts/yt-search.sh "home lab setup" --months 24
```

## Interpreting the Engagement Ratio

The views-to-subscribers ratio helps identify standout content:

- **> 1.0x** — The video got more views than the channel has subscribers. Strong signal that the topic resonated or the algorithm boosted it.
- **0.3x - 1.0x** — Typical range for established channels.
- **< 0.3x** — Below average reach. Could mean the topic is niche, the thumbnail/title underperformed, or the channel's audience has moved on.

This metric is most useful for comparing videos on the same topic — a 5.0x ratio on a small channel often means the content hit a nerve.

## How Claude Should Use This

When the user asks to search YouTube or find videos:

1. Run the script with the user's query and any specified flags
2. Present the results — the script output is already formatted for terminal reading
3. If the user wants analysis (e.g., "which of these are worth watching?"), use the engagement ratio and view counts to highlight standouts
4. If subscriber count shows "N/A" for many results, that's normal — yt-dlp can't always fetch channel metadata from search results

## Troubleshooting

- **No results**: Try broadening the query or increasing `--months`
- **Slow**: Each result requires a metadata fetch. Reduce `--count` for faster results.
- **"N/A" for subscribers**: yt-dlp sometimes can't resolve channel follower counts from search. The other fields will still populate.
