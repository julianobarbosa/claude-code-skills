#!/usr/bin/env python3
"""
adapt_prompts.py — fill the 9 base prompt templates with topic-specific facts.

Reads the base templates from references/prompt-library.md (or a JSON facts
file passed in) and emits a ready-to-save markdown document with placeholders
replaced. The emitted document is suitable for:
  1. Saving locally under MEMORY/WORK/<slug>/prompts.md
  2. Passing as text to mcp__notebooklm-rpc__notebook_add_text

Usage:
  python scripts/adapt_prompts.py --facts facts.json

facts.json schema:
  {
    "topic": "cmux",
    "central_theme": "native macOS terminal for AI coding agents",
    "key_concepts": "libghostty rendering, OSC notifications, claude-teams",
    "key_facts": "YC S24, launched Feb 2026, ~15k stars, #2 on HN",
    "origin_story": "Austin Wang and Lawrence Chen built it after frustration with generic 'Claude is waiting' notifications",
    "implications": "positions as a terminal substrate, not an orchestrator",
    "key_concepts_list": "libghostty, OSC 9/99/777, claude-teams, Ghostty config, vertical tabs, notification rings, remote workspaces, AGPL",
    "expected_queries": "cmux, terminal for Claude Code, parallel AI agents macOS"
  }
"""

import argparse
import json
import sys
from pathlib import Path

TEMPLATES = {
    1: (
        "Five Essential Questions (XDA #1)",
        """1.) Analyze all sources in this notebook about {topic} and generate 5 essential questions that, when answered, capture the main points and core meaning of the material.
2.) When formulating your questions:
   a. Address the central theme — {central_theme}
   b. Identify key supporting ideas ({key_concepts})
   c. Highlight important facts or evidence ({key_facts})
   d. Reveal the creators' purpose or perspective ({origin_story})
   e. Explore significant implications — {implications}
3.) Answer all 5 questions one-by-one in detail, citing specific sources.""",
    ),
    2: (
        "Find the Interesting Bits (XDA #2)",
        """What are the most surprising or interesting pieces of information or narratives in these sources about {topic}? Focus on:
- Counter-intuitive design decisions
- Verbatim quotes from the creators, notable endorsers, or commenters
- Unexpected community dynamics
- Technical choices that differ from conventional wisdom
- Quotable lines that capture {topic}'s identity

Include at least 8 key quotes with attribution.""",
    ),
    3: (
        "Quiz Show (XDA #3)",
        """You're hosting a fun quiz show with two hosts. The first host quizzes the second on concepts from this notebook about {topic}. Include a mix of multiple choice and true/false questions covering: {key_concepts_list}.

Occasionally, the second host should get an answer wrong, and the first host should step in to explain the correct answer clearly, quoting sources. At the end, share the final score and a brief summary of how the second host did.""",
    ),
    4: (
        "Content Analyst Report (AI Fire #1)",
        """Act as a content strategy expert. Based on the sources in this notebook about {topic}, create a full analysis with:

**1. Quick Summary:** 3 bullet points summarizing the most important ideas.

**2. Deep Analysis:**
   - Target Audience: Who is {topic} for? Be specific.
   - Main Arguments: List the 3 main arguments {topic} makes.
   - Best Quotes: 3 powerful sentences or facts from the sources, with attribution.

**3. Creative Ideas:**
   - Alternative Taglines: 2 other taglines (one curiosity-driven, one benefit-driven).
   - Social Media: A short LinkedIn post and a tweet/X post, with hashtags.""",
    ),
    5: (
        "Community → Action Plan (AI Fire #2)",
        """Act as a professional project secretary. Based on the community discussion sources in this notebook (forums, issues, threads), treat the collective conversation as a {topic} product meeting. Create a markdown summary with:

**1. Goal of the Meeting:** One sentence — what is the community collectively asking {topic} to solve next?

**2. Main Voices:** Key speakers with handles/attribution.

**3. Summary of Main Discussions:** Main topics across threads.

**4. Important Decisions Made:** Concrete commitments maintainers announced.

**5. To-Do List:** Table with Task | Likely Owner | Priority for community-requested improvements.

**6. Unresolved Issues:** Open questions.""",
    ),
    6: (
        "SEO Outline (AI Fire #3)",
        """Act as an SEO expert and content editor. Based on ALL sources in this notebook about {topic}:

**Part A: Competitor & Landscape Analysis**
1. Search Intent: When people search for {expected_queries}, what do they actually want?
2. Common Topics: 5 sub-topics every existing article/thread covers.
3. Content Gaps: Important sub-topics that are under-covered.

**Part B: Outline for a New Article**
1. 3 H1 suggestions (curiosity, benefit, authority).
2. Full H2/H3 structure including a gap-filling section from Part A.
3. Writer notes under each heading with specific facts/quotes/data from the notebook.""",
    ),
    7: (
        "360° Feedback on Marketing (AI Fire #4)",
        """Create a "360-Degree Feedback Report" for the {topic} README/homepage/marketing content captured in this notebook. Include:

**Section 1: Strict Editor's View**
   - 3 longest or weakest sentences with shorter rewrites.
   - Weakest claim — what needs more proof?

**Section 2: New Reader's View**
   - Confusing terms/concepts for someone new to the domain.
   - Most boring section. Why?

**Section 3: Marketing Expert's View**
   - Is the opening hook strong enough? If not, rewrite.
   - Stronger call-to-action for the end.""",
    ),
    8: (
        "Study Guide Kit (AI Fire #5)",
        """Act as a dedicated tutor for someone onboarding to {topic}. Based on all sources, create a "Complete Study Guide Kit":

**1. Summary of Key Concepts:**
   The 5 most important ideas in {topic}, each explained simply with a specific example from the sources.

**2. Terminology Flashcards:**
   12 important terms with short definitions. Format: "Term: Definition."

**3. Practice Questions:**
   - 5 essay-style questions covering architecture, philosophy, comparison, limitations, extensibility.
   - 10-question multiple-choice quiz (A, B, C, D).

**4. Answer Key:** Answers for the 10 MCQs with one-sentence rationale each, citing sources.""",
    ),
    9: (
        "Conference Talk Script (AI Fire #6)",
        """Act as a developer/product-advocate coach. I'm preparing a 15-minute conference talk about {topic}, positioned as a maintainer or power user. Based on all sources, create a "Talk Prep Plan":

**Part 1: Audience Fit Analysis**
   3 biggest matches between {topic}'s design choices and real pains evidenced in the community sources.

**Part 2: Talk Script**
   - 3–4 sentence opening hook naming the specific pain and pivoting to the {topic} answer.
   - 3 "story moments" from the sources in STAR format (Situation, Task, Action, Result).

**Part 3: Audience Q&A Prep**
   3 smart questions the audience will likely ask, with grounded answers using direct source quotes.""",
    ),
}


REQUIRED_KEYS = [
    "topic", "central_theme", "key_concepts", "key_facts",
    "origin_story", "implications", "key_concepts_list", "expected_queries",
]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--facts", required=True, help="Path to facts.json")
    p.add_argument("--out", default="-", help="Output path (default: stdout)")
    args = p.parse_args()

    facts = json.loads(Path(args.facts).read_text())
    missing = [k for k in REQUIRED_KEYS if k not in facts]
    if missing:
        print(f"ERROR: facts.json missing keys: {missing}", file=sys.stderr)
        return 1

    out_lines = [
        f"# {facts['topic']} :: docs — 9 Curated NotebookLM Prompts",
        "",
        "Paste any of these into the NotebookLM chat for this notebook.",
        "Prompts 1–3 adapted from XDA Developers; prompts 4–9 adapted from AI Fire.",
        "",
        "- XDA: https://www.xda-developers.com/prompts-i-use-to-get-most-out-of-noteboooklm/",
        "- AI Fire: https://www.aifire.co/p/6-notebooklm-prompts-that-do-your-hard-work-for-you",
        "",
        "---",
        "",
    ]
    for num, (title, body) in TEMPLATES.items():
        filled = body.format(**facts)
        out_lines.append(f"## Prompt {num} — {title}")
        out_lines.append("")
        out_lines.append(filled)
        out_lines.append("")
        out_lines.append("---")
        out_lines.append("")

    text = "\n".join(out_lines)
    if args.out == "-":
        print(text)
    else:
        Path(args.out).write_text(text)
        print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
