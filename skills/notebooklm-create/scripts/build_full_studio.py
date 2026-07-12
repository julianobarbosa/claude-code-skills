#!/usr/bin/env python3
"""
build_full_studio.py — plan-printer for the full NotebookLM Studio dispatch.

Emits the ordered, topic-customized MCP call plan for generating all 10
Studio artifact types. Claude executes each line as a separate MCP tool call.

The order is tuned to minimize wall-clock time: async media first (audio,
video, infographic, slide deck), then synchronous/fast-async artifacts.

Each call includes confirm=true; user approval MUST be obtained before
executing the emitted plan.

Usage:
  python scripts/build_full_studio.py \\
    --notebook-id NB_UUID \\
    --topic "cmux" \\
    --theme "native macOS terminal for parallel AI coding agents" \\
    --features "libghostty rendering,notification rings,claude-teams,remote workspaces" \\
    --comparison "tmux,Agent Orchestrator,T3 Code,OpenAI Symphony" \\
    --audience "macOS developers running parallel Claude Code / Codex sessions"
"""

import argparse
import sys


STUDIO_PLAN = [
    # (mcp_tool_name, kwargs_template)
    # --- Async media first (longest rendering) ---
    (
        "audio_overview_create",
        lambda t: dict(
            notebook_id=t["notebook_id"],
            format="deep_dive",
            length="default",
            language="en",
            focus_prompt=(
                f"Focus on {t['topic']}: {t['theme']}. Why it was built, key features "
                f"({t['features']}), and comparison to {t['comparison']}. Audience: {t['audience']}."
            ),
            confirm=True,
        ),
    ),
    (
        "video_overview_create",
        lambda t: dict(
            notebook_id=t["notebook_id"],
            format="explainer",
            visual_style="auto_select",
            language="en",
            focus_prompt=(
                f"Explain {t['topic']} visually: the problem it solves, architecture, "
                f"key features ({t['features']}), and traction."
            ),
            confirm=True,
        ),
    ),
    (
        "infographic_create",
        lambda t: dict(
            notebook_id=t["notebook_id"],
            orientation="portrait",
            detail_level="detailed",
            language="en",
            focus_prompt=(
                f"Visual overview of {t['topic']}: key features ({t['features']}), "
                f"traction metrics, architecture layering, community sentiment themes."
            ),
            confirm=True,
        ),
    ),
    (
        "slide_deck_create",
        lambda t: dict(
            notebook_id=t["notebook_id"],
            format="detailed_deck",
            length="default",
            language="en",
            focus_prompt=(
                f"A presentation on {t['topic']}: the problem, the solution, architecture "
                f"deep-dive, comparison to {t['comparison']}, installation, traction, limitations."
            ),
            confirm=True,
        ),
    ),
    # --- Synchronous / fast-async ---
    (
        "mind_map_create",
        lambda t: dict(
            notebook_id=t["notebook_id"],
            title=f"{t['topic']} Architecture & Ecosystem",
            confirm=True,
        ),
    ),
    (
        "report_create",
        lambda t: dict(
            notebook_id=t["notebook_id"],
            report_format="Briefing Doc",
            language="en",
            confirm=True,
        ),
    ),
    (
        "report_create",
        lambda t: dict(
            notebook_id=t["notebook_id"],
            report_format="Study Guide",
            language="en",
            confirm=True,
        ),
    ),
    (
        "flashcards_create",
        lambda t: dict(
            notebook_id=t["notebook_id"],
            difficulty="medium",
            confirm=True,
        ),
    ),
    (
        "quiz_create",
        lambda t: dict(
            notebook_id=t["notebook_id"],
            question_count=10,
            difficulty="medium",
            confirm=True,
        ),
    ),
    (
        "data_table_create",
        lambda t: dict(
            notebook_id=t["notebook_id"],
            description=(
                f"Comparison table: {t['topic']} vs {t['comparison']}. Columns: Tool, "
                f"Layer, Platform, Key differentiator, License. Include a one-line "
                f"source quote per row."
            ),
            language="en",
            confirm=True,
        ),
    ),
]


def fmt_kwargs(kwargs: dict) -> str:
    parts = []
    for k, v in kwargs.items():
        if isinstance(v, bool):
            parts.append(f"{k}={str(v).lower()}")
        elif isinstance(v, (int, float)):
            parts.append(f"{k}={v}")
        else:
            escaped = str(v).replace('"', '\\"')
            parts.append(f'{k}="{escaped}"')
    return ", ".join(parts)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--notebook-id", required=True)
    p.add_argument("--topic", required=True)
    p.add_argument("--theme", required=True, help="One-line topic identity")
    p.add_argument("--features", required=True, help="Comma-separated key features")
    p.add_argument("--comparison", required=True, help="Comma-separated comparable tools")
    p.add_argument("--audience", required=True, help="Target audience")
    args = p.parse_args()

    topic_ctx = dict(
        notebook_id=args.notebook_id,
        topic=args.topic,
        theme=args.theme,
        features=args.features,
        comparison=args.comparison,
        audience=args.audience,
    )

    print(f"# Full Studio dispatch plan for {args.topic}")
    print(f"# Notebook: {args.notebook_id}")
    print("# OBTAIN USER APPROVAL before executing these calls.")
    print()

    for tool, kwargs_fn in STUDIO_PLAN:
        kwargs = kwargs_fn(topic_ctx)
        print(f"CALL: mcp__notebooklm-rpc__{tool}({fmt_kwargs(kwargs)})")

    print()
    print("# After dispatch, wait 45s then call:")
    print(f'CALL: mcp__notebooklm-rpc__studio_status(notebook_id="{args.notebook_id}")')
    print("# Poll again 2-3 min later for async media (audio/video/infographic/slide deck).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
