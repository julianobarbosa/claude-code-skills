#!/usr/bin/env python3
"""Idempotent, paced NotebookLM persona configurator and full Studio generator."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_PERSONA = (
    "Atue como analista técnico sênior. Responda SEMPRE em português brasileiro (pt-BR). "
    "Use terminologia técnica em português; deixe siglas/protocolos/comandos em inglês "
    "quando o termo técnico for o original. Citações inline [1], [2] permanecem como estão. "
    "Não traduza nomes próprios, nomes de produto, nem trechos de código/CLI/JSON/YAML. "
    "Quando uma afirmação não tiver suporte explícito nas fontes do notebook, marque com "
    "[NÃO VERIFICADO] e explique o que faltaria para verificar."
)
DEFAULT_RESPONSE_LENGTH = "longer"


def extract_notebook_id(raw: str) -> str:
    m = re.search(r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})", raw)
    return m.group(1) if m else raw.strip()


def run_cli(args: list[str], dry_run: bool = False) -> tuple[int, dict | str]:
    cmd = ["notebooklm", *args]
    if dry_run:
        print(f"[DRY-RUN] {' '.join(cmd)}")
        return 0, {"dry_run": True}
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = proc.stdout.strip()
    try:
        return proc.returncode, json.loads(out) if out else {}
    except json.JSONDecodeError:
        return proc.returncode, out or proc.stderr.strip()


def classify_existing(artifacts: list[dict]) -> dict[str, dict]:
    """Map canonical studio keys to existing artifact records (completed or in_progress)."""
    found: dict[str, dict] = {}
    for art in artifacts:
        t_id = (art.get("type_id") or "").lower()
        t_label = (art.get("type") or "").lower()
        title = (art.get("title") or "").lower()
        if t_id == "audio":
            found.setdefault("audio", art)
        elif t_id == "video":
            found.setdefault("video", art)
        elif t_id == "infographic":
            found.setdefault("infographic", art)
        elif t_id == "slide_deck":
            found.setdefault("slide-deck", art)
        elif t_id == "mind_map":
            found.setdefault("mind-map", art)
        elif t_id == "flashcards":
            found.setdefault("flashcards", art)
        elif t_id == "quiz":
            found.setdefault("quiz", art)
        elif t_id == "data_table":
            found.setdefault("table-report", art)
        elif t_id == "report":
            if t_label == "briefing doc" or "briefing" in title:
                found.setdefault("briefing-doc", art)
            elif "guia de estudo" in title or "study guide" in title:
                found.setdefault("study-guide", art)
            elif "comparativo técnico" in title or "tabela" in title:
                found.setdefault("table-report", art)
            else:
                found.setdefault("blog-post", art)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", "--notebook", required=True, help="Notebook URL or UUID")
    parser.add_argument("-f", "--focus", required=True, help="1-2 sentence topic focus (in pt-BR)")
    parser.add_argument("--persona-config", default="persona_config.json", help="Path to persona_config.json")
    parser.add_argument("--lang", default="pt_BR", help="Output language code (default: pt_BR)")
    parser.add_argument("--delay", type=float, default=1.5, help="Seconds between CLI calls (default: 1.5)")
    parser.add_argument("--only", default="", help="Comma-separated subset of artifact keys")
    parser.add_argument("--try-native-table", action="store_true", help="Try native data-table before custom report")
    parser.add_argument("--force", action="store_true", help="Regenerate even if artifact already exists")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    args = parser.parse_args()

    nb = extract_notebook_id(args.notebook)
    focus = args.focus.strip()
    lang = args.lang

    # 1. Load persona_config.json if available
    persona = DEFAULT_PERSONA
    resp_len = DEFAULT_RESPONSE_LENGTH
    cfg_path = Path(args.persona_config)
    if cfg_path.is_file():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        persona = cfg.get("persona") or persona
        resp_len = cfg.get("response_length") or resp_len

    print(f"==> [1/4] Setting active context & configuring persona on {nb}...")
    run_cli(["use", nb], dry_run=args.dry_run)
    rc, cfg_out = run_cli(
        ["configure", "-n", nb, "--response-length", resp_len, "--persona", persona, "--json"],
        dry_run=args.dry_run,
    )
    if rc != 0:
        print(f"WARN: configure returned {rc}: {cfg_out}", file=sys.stderr)

    # 2. Inspect existing artifacts for idempotency
    print("==> [2/4] Inspecting existing Studio artifacts...")
    _, list_out = run_cli(["artifact", "list", "-n", nb, "--json"], dry_run=args.dry_run)
    existing_list = list_out.get("artifacts", []) if isinstance(list_out, dict) else []
    existing_map = classify_existing(existing_list)

    specs: list[tuple[str, list[str]]] = [
        ("audio", ["generate", "audio", "-n", nb, "--format", "deep-dive", "--length", "default", "--language", lang, f"Foque em: {focus}", "--json"]),
        ("video", ["generate", "video", "-n", nb, "--format", "explainer", "--style", "auto", "--language", lang, f"Explique visualmente: {focus}", "--json"]),
        ("infographic", ["generate", "infographic", "-n", nb, "--orientation", "landscape", "--detail", "detailed", "--language", lang, f"Visão geral comparativa e arquitetural sobre: {focus}", "--json"]),
        ("slide-deck", ["generate", "slide-deck", "-n", nb, "--format", "detailed", "--length", "default", "--language", lang, f"Apresentação técnica completa sobre: {focus}", "--json"]),
        ("briefing-doc", ["generate", "report", "-n", nb, "--format", "briefing-doc", "--language", lang, "--append", f"Responda em português brasileiro (pt-BR). Foque em: {focus}", "--json"]),
        ("study-guide", ["generate", "report", "-n", nb, "--format", "study-guide", "--language", lang, "--append", f"Responda em português brasileiro (pt-BR). Foque nos conceitos-chave, arquitetura e prática: {focus}", "--json"]),
        ("blog-post", ["generate", "report", "-n", nb, "--format", "blog-post", "--language", lang, "--append", f"Responda em português brasileiro (pt-BR). Artigo técnico sobre: {focus}", "--json"]),
        ("flashcards", ["generate", "flashcards", "-n", nb, "--difficulty", "medium", "--quantity", "standard", f"Em português brasileiro (pt-BR): conceitos-chave e arquitetura sobre {focus}.", "--json"]),
        ("quiz", ["generate", "quiz", "-n", nb, "--difficulty", "medium", "--quantity", "more", f"Em português brasileiro (pt-BR): perguntas técnicas e práticas sobre {focus}.", "--json"]),
        ("mind-map", ["generate", "mind-map", "-n", nb, "--language", lang, "--instructions", f"Mapa mental em português brasileiro (pt-BR) cobrindo: {focus}.", "--json"]),
        ("table-report", ["generate", "report", "-n", nb, "--format", "custom", "--language", lang, f"Crie uma Tabela de Dados comparativa completa em português brasileiro (pt-BR) estruturada em formato tabular Markdown sobre {focus}, incluindo colunas para Componente/Critério, Funcionalidades, Performance/Latência, UX, Vantagens e Limitações.", "--json"]),
    ]

    only_set = {k.strip() for k in args.only.split(",") if k.strip()}
    print(f"==> [3/4] Dispatching Studio artifacts (pacing={args.delay}s)...")
    for key, cmd_args in specs:
        if only_set and key not in only_set:
            continue
        prev = existing_map.get(key)
        if prev and not args.force:
            status = prev.get("status")
            art_id = prev.get("id")
            if status in ("completed", "in_progress", "pending"):
                print(f"  [SKIP] {key}: already {status} (id={art_id})")
                continue
            if status == "failed" and art_id:
                print(f"  [RETRY] {key}: retrying failed artifact {art_id}")
                run_cli(["artifact", "retry", art_id, "-n", nb, "--json"], dry_run=args.dry_run)
                time.sleep(args.delay)
                continue

        if key == "table-report" and args.try_native_table:
            rc_dt, _ = run_cli(
                ["generate", "data-table", "-n", nb, "--language", lang, f"Tabela comparativa sobre {focus}", "--json"],
                dry_run=args.dry_run,
            )
            if rc_dt == 0:
                print("  [OK] table-report (native data-table)")
                time.sleep(args.delay)
                continue
            print("  [FALLBACK] native data-table rejected (rpc_code=3); generating custom tabular report...")

        rc, out = run_cli(cmd_args, dry_run=args.dry_run)
        status_str = "OK" if rc == 0 else f"ERR({rc})"
        print(f"  [{status_str}] {key}: {out if isinstance(out, dict) else str(out)[:120]}")
        if not args.dry_run:
            time.sleep(args.delay)

    print("==> [4/4] Fetching final Studio status...")
    _, final_out = run_cli(["artifact", "list", "-n", nb, "--json"], dry_run=args.dry_run)
    print(json.dumps(final_out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
