# Prompt Library — 9 curated NotebookLM chat prompts

Base templates for the 9 prompts this skill adds to every topic notebook. Three from XDA Developers, six from AI Fire. Adapted to be topic-agnostic — replace `{TOPIC}`, `{CENTRAL_THEME}`, `{KEY_FACTS}`, `{KEY_ACTORS}`, etc. with the topic-specific facts from Phase 2 research.

**Attribution (preserve when adapting):**
- Prompts 1–3: Alex Blake, XDA Developers, "3 prompts I use to get the most out of NotebookLM" — https://www.xda-developers.com/prompts-i-use-to-get-most-out-of-noteboooklm/
- Prompts 4–9: AI Fire, "6 NotebookLM Prompts That Do Your Hard Work For You" — https://www.aifire.co/p/6-notebooklm-prompts-that-do-your-hard-work-for-you

---

## Prompt 1 — Five Essential Questions (XDA #1)

```
1.) Analyze all sources in this notebook about {TOPIC} and generate 5 essential questions that, when answered, capture the main points and core meaning of the material.
2.) When formulating your questions:
   a. Address the central theme — {CENTRAL_THEME}
   b. Identify key supporting ideas ({KEY_CONCEPTS})
   c. Highlight important facts or evidence ({KEY_FACTS})
   d. Reveal the creators' purpose or perspective ({ORIGIN_STORY})
   e. Explore significant implications — {IMPLICATIONS}
3.) Answer all 5 questions one-by-one in detail, citing specific sources.
```

## Prompt 2 — Find the Interesting Bits (XDA #2)

```
What are the most surprising or interesting pieces of information or narratives in these sources about {TOPIC}? Focus on:
- Counter-intuitive design decisions
- Verbatim quotes from the creators, notable endorsers, or commenters
- Unexpected community dynamics
- Technical choices that differ from conventional wisdom
- Quotable lines that capture {TOPIC}'s identity

Include at least 8 key quotes with attribution.
```

## Prompt 3 — Quiz Show (XDA #3)

```
You're hosting a fun quiz show with two hosts. The first host quizzes the second on concepts from this notebook about {TOPIC}. Include a mix of multiple choice and true/false questions covering: {KEY_CONCEPTS_LIST}.

Occasionally, the second host should get an answer wrong, and the first host should step in to explain the correct answer clearly, quoting sources. At the end, share the final score and a brief summary of how the second host did.
```

## Prompt 4 — Content Analyst Report (AI Fire #1)

```
Act as a content strategy expert. Based on the sources in this notebook about {TOPIC}, create a full analysis with:

**1. Quick Summary:** 3 bullet points summarizing the most important ideas.

**2. Deep Analysis:**
   - Target Audience: Who is {TOPIC} for? Be specific.
   - Main Arguments: List the 3 main arguments {TOPIC} makes.
   - Best Quotes: 3 powerful sentences or facts from the sources, with attribution.

**3. Creative Ideas:**
   - Alternative Taglines: 2 other taglines (one curiosity-driven, one benefit-driven).
   - Social Media: A short LinkedIn post and a tweet/X post, with hashtags.
```

## Prompt 5 — Community → Action Plan (AI Fire #2)

```
Act as a professional project secretary. Based on the community discussion sources in this notebook (forums, issues, threads), treat the collective conversation as a product meeting. Create a markdown summary with:

**1. Goal of the Meeting:** One sentence — what is the community collectively asking {TOPIC} to solve next?

**2. Main Voices:** Key speakers with handles/attribution.

**3. Summary of Main Discussions:** Main topics across threads.

**4. Important Decisions Made:** Concrete commitments maintainers announced.

**5. To-Do List:** Table with Task | Likely Owner | Priority for community-requested improvements.

**6. Unresolved Issues:** Open questions.
```

## Prompt 6 — SEO Outline (AI Fire #3)

```
Act as an SEO expert and content editor. Based on ALL sources in this notebook about {TOPIC}:

**Part A: Competitor & Landscape Analysis**
1. Search Intent: When people search {EXPECTED_QUERIES}, what do they actually want?
2. Common Topics: 5 sub-topics every existing article/thread covers.
3. Content Gaps: Important sub-topics that are under-covered.

**Part B: Outline for a New Article**
1. 3 H1 suggestions (curiosity, benefit, authority).
2. Full H2/H3 structure including a gap-filling section from Part A.
3. Writer notes under each heading with specific facts/quotes/data from the notebook.
```

## Prompt 7 — 360° Feedback on Marketing (AI Fire #4)

```
Create a "360-Degree Feedback Report" for the {TOPIC} README/homepage/marketing content captured in this notebook. Include:

**Section 1: Strict Editor's View**
   - 3 longest or weakest sentences with shorter rewrites.
   - Weakest claim — what needs more proof?

**Section 2: New Reader's View**
   - Confusing terms/concepts for someone new to the domain.
   - Most boring section. Why?

**Section 3: Marketing Expert's View**
   - Is the opening hook strong enough? If not, rewrite.
   - Stronger call-to-action for the end.
```

## Prompt 8 — Study Guide Kit (AI Fire #5)

```
Act as a dedicated tutor for someone onboarding to {TOPIC}. Based on all sources, create a "Complete Study Guide Kit":

**1. Summary of Key Concepts:**
   The 5 most important ideas in {TOPIC}, each explained simply with a specific example from the sources.

**2. Terminology Flashcards:**
   12 important terms with short definitions. Format: "Term: Definition."

**3. Practice Questions:**
   - 5 essay-style questions covering architecture, philosophy, comparison, limitations, extensibility.
   - 10-question multiple-choice quiz (A, B, C, D).

**4. Answer Key:** Answers for the 10 MCQs with one-sentence rationale each, citing sources.
```

## Prompt 9 — Conference Talk Script (AI Fire #6, adapted)

```
Act as a developer/product-advocate coach. I'm preparing a 15-minute conference talk about {TOPIC}, positioned as a maintainer or power user. Based on all sources, create a "Talk Prep Plan":

**Part 1: Audience Fit Analysis**
   3 biggest matches between {TOPIC}'s design choices and real pains evidenced in the community sources.

**Part 2: Talk Script**
   - 3–4 sentence opening hook naming the specific pain and pivoting to the {TOPIC} answer.
   - 3 "story moments" from the sources in STAR format (Situation, Task, Action, Result).

**Part 3: Audience Q&A Prep**
   3 smart questions the audience will likely ask, with grounded answers using direct source quotes.
```

---

## Adaptation checklist

When adapting for a specific topic, replace:

- `{TOPIC}` — the project/subject name
- `{CENTRAL_THEME}` — one-line identity statement
- `{KEY_CONCEPTS}` — 4–6 technical sub-concepts
- `{KEY_FACTS}` — 3–5 verifiable data points (version, launch date, stars, funding)
- `{ORIGIN_STORY}` — who built it and why (one sentence)
- `{IMPLICATIONS}` — what layering/positioning matters
- `{KEY_CONCEPTS_LIST}` — comma-separated list for Quiz Show
- `{EXPECTED_QUERIES}` — 2–3 likely search queries

Replace every placeholder. Generic prompts produce generic outputs.
