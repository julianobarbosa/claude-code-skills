---
name: repo-to-gem
description: Ingests a GitHub repo or documentation subfolder, bundles it into a knowledge digest, and generates the complete Gem/GPT system prompt and setup manifest.
version: 1.0.0
triggers:
  - "/repo-to-gem"
  - "transform repo to gem"
  - "create gem from repo"
inputs:
  repo_url:
    type: string
    description: "URL of the GitHub repo or subfolder (e.g., https://github.com/org/repo/tree/main/docs)"
    required: true
  gem_name:
    type: string
    description: "Display name for the Gem (optional, derived from repo if omitted)"
    required: false
---

# Repo-to-Gem Workflow Skill

## Objective
Convert a GitHub codebase or documentation directory into an optimized, self-contained Knowledge Pack and System Instruction prompt for a Google Gemini custom Gem.

---

## Execution Steps

### Step 1: Ingest & Flatten the Source
1. Parse the target repository URL:
   - If a specific `/tree/main/...` path is provided, isolate that subdirectory.
2. Select the ingestion method:
   - **CLI Method (Default):**
     ```bash
     npx repomix <target-directory> --style xml --output gem-knowledge-bundle.txt
     ```
   - **Web/Fallback Method:**
     Direct the user to fetch via `gitingest.com/<org>/<repo>/tree/<branch>/<path>` to download the consolidated plain-text bundle.
3. Verify token overhead:
   - Keep the flattened bundle under 500k tokens for optimal Gem retrieval latency.
   - Ignore lockfiles (`package-lock.json`, `pnpm-lock.yaml`), build outputs (`dist/`, `build/`), and media binaries.

---

### Step 2: Extract Architecture & Taxonomy
Scan the ingested documentation bundle to identify:
- **Core Domain & Purpose:** What framework, tool, or methodology is described?
- **Key Concepts & Glossary:** Distinct terminology, acronyms, and operational phases (e.g., Analysis, Plan, Implement, Verify).
- **Core Workflows & Schemas:** Primary artifact formats (e.g., `SPEC.md`, config JSONs, CLI syntax).
- **Hard Constraints & Anti-Patterns:** What the AI assistant must NOT hallucinate or alter.

---

### Step 3: Generate System Instructions (Prompt Artifact)
Generate a structured, Markdown-formatted prompt using the following template:

```markdown
# Role & Purpose
You are an expert AI advisor and system architect specialized exclusively in {{TOPIC_NAME}}.
Your role is to guide developers, verify architectures, and produce standard artifacts following the provided Knowledge base.

# Grounding & Knowledge Rules
1. Always ground operational advice in the uploaded Knowledge files.
2. If an artifact structure or syntax is specified in the knowledge base, adhere to it strictly.
3. If asked about features or versions outside the documentation scope, explicitly flag that it is not covered.

# Methodology & Core Workflows
{{WORKFLOW_STAGES_OR_PIPELINES}}

# Artifact & Output Standards
{{SPEC_FORMATS_AND_TEMPLATES}}

# Tone & Interaction Style
- Concise, technical, and developer-centric.
- Lead directly with actionable recommendations, code blocks, or spec diffs.
- Avoid robotic conversational preambles.