#!/usr/bin/env python3
"""Idempotent, paced NotebookLM persona configurator and full Studio generator."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
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

SUPPORTED_KEYS: tuple[str, ...] = (
    "audio",
    "video",
    "infographic",
    "slide-deck",
    "briefing-doc",
    "study-guide",
    "blog-post",
    "flashcards",
    "quiz",
    "mind-map",
    "table-report",
)

USABLE_STATUSES: frozenset[str] = frozenset({"completed", "in_progress", "pending"})


def extract_notebook_id(raw: str) -> str:
    m = re.search(
        r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})",
        raw,
    )
    return m.group(1) if m else raw.strip()


@contextmanager
def notebook_lock(notebook_id: str) -> Iterator[Path]:
    """Serialize runs targeting the same notebook to prevent concurrent duplicate dispatches."""
    state_dir = Path(tempfile.gettempdir()) / "notebooklm-studio"
    state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = state_dir / f"{notebook_id}.lock"
    with lock_path.open("w", encoding="utf-8") as fh:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(
                f"==> Waiting for active notebooklm-studio lock on {notebook_id} ({lock_path})...",
                file=sys.stderr,
            )
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield state_dir
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


class PacedCLI:
    """Executes notebooklm CLI invocations with a guaranteed minimum delay between calls."""

    def __init__(self, delay: float, dry_run: bool = False) -> None:
        self.delay = max(0.0, delay)
        self.dry_run = dry_run
        self._last_call_ts: float | None = None

    def run(self, args: list[str]) -> tuple[int, dict | str]:
        cmd = ["notebooklm", *args]
        if self.dry_run:
            print(f"[DRY-RUN] {' '.join(cmd)}")
            return 0, {"dry_run": True, "artifacts": [], "sources": []}
        if self._last_call_ts is not None and self.delay > 0:
            elapsed = time.monotonic() - self._last_call_ts
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self._last_call_ts = time.monotonic()
        out = proc.stdout.strip()
        err = proc.stderr.strip()
        if not out:
            return proc.returncode, err
        try:
            return proc.returncode, json.loads(out)
        except json.JSONDecodeError:
            return proc.returncode, out


def fetch_artifacts(cli: PacedCLI, nb: str) -> tuple[bool, list[dict]]:
    """Fetch and validate the artifact list; return (ok, artifacts)."""
    rc, out = cli.run(["artifact", "list", "-n", nb, "--json"])
    artifacts = out.get("artifacts") if isinstance(out, dict) else None
    if (
        rc != 0
        or not isinstance(out, dict)
        or not isinstance(artifacts, list)
        or any(
            not isinstance(art, dict)
            or not isinstance(art.get("id"), str)
            or not art["id"]
            or not isinstance(art.get("status"), str)
            or not isinstance(art.get("type_id"), str)
            or not art["type_id"]
            or not isinstance(art.get("title"), str)
            or (art.get("type") is not None and not isinstance(art.get("type"), str))
            for art in artifacts
        )
    ):
        print(
            f"ERROR: 'notebooklm artifact list' failed (rc={rc}): {out}",
            file=sys.stderr,
        )
        return False, []
    return True, artifacts


def fetch_sources_fingerprint(
    cli: PacedCLI,
    nb: str,
    focus: str,
    lang: str,
    persona: str,
    response_length: str,
) -> tuple[bool, str]:
    """Fingerprint source metadata and all configured output-affecting inputs."""
    rc, out = cli.run(["source", "list", "-n", nb, "--json"])
    if rc != 0 or not isinstance(out, dict) or not isinstance(out.get("sources"), list):
        print(
            f"ERROR: 'notebooklm source list' failed (rc={rc}): {out}",
            file=sys.stderr,
        )
        return False, ""
    sources = out["sources"]
    if any(not isinstance(source, dict) or not source.get("id") for source in sources):
        print(
            f"ERROR: 'notebooklm source list' returned an unexpected source row: {out}",
            file=sys.stderr,
        )
        return False, ""
    source_fields = (
        "id",
        "title",
        "type",
        "url",
        "status",
        "status_id",
        "created_at",
        "drive_document_id",
        "drive_status",
        "is_drive_degraded",
    )
    source_state = sorted(
        ({field: source.get(field) for field in source_fields} for source in sources),
        key=lambda source: str(source["id"]),
    )
    payload = json.dumps(
        {
            "sources": source_state,
            "focus": focus,
            "lang": lang,
            "persona": persona,
            "response_length": response_length,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return True, hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def artifact_input_fingerprint(
    base_fingerprint: str,
    key: str,
    command: list[str],
    native_table_command: list[str] | None = None,
) -> str:
    """Include each artifact's actual generation recipe in its input fingerprint."""
    payload = json.dumps(
        {
            "base": base_fingerprint,
            "key": key,
            "command": command,
            "native_table_command": native_table_command,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def wait_for_audio_completion(
    cli: PacedCLI,
    notebook_id: str,
    audio_id: str | None,
    timeout: int,
    next_action: str,
) -> bool:
    """Block a subsequent media generation until in-flight audio is terminal."""
    if not audio_id:
        print(
            f"  [ERR] Cannot verify audio completion before {next_action}: "
            "no audio artifact ID is available.",
            file=sys.stderr,
        )
        return False
    print(
        f"  [WAIT] Waiting for audio ({audio_id}) before {next_action} "
        "to avoid concurrent media rate limits..."
    )
    rc, out = cli.run(
        [
            "artifact",
            "wait",
            audio_id,
            "-n",
            notebook_id,
            "--timeout",
            str(timeout),
            "--json",
        ]
    )
    if rc != 0:
        print(
            f"  [ERR] audio wait returned rc={rc} ({out}); {next_action} was not dispatched.",
            file=sys.stderr,
        )
        return False
    return True


def load_manifest(state_dir: Path, nb: str) -> dict:
    path = state_dir / f"{nb}.manifest.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def save_manifest(state_dir: Path, nb: str, manifest: dict) -> None:
    path = state_dir / f"{nb}.manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def _select_artifact(found: dict[str, dict], key: str, candidate: dict) -> None:
    """Record `candidate` for `key`, ensuring completed/active records take precedence over failed ones."""
    existing = found.get(key)
    if existing is None:
        found[key] = candidate
        return
    existing_status = (existing.get("status") or "").lower()
    candidate_status = (candidate.get("status") or "").lower()
    if existing_status not in USABLE_STATUSES and candidate_status in USABLE_STATUSES:
        found[key] = candidate


def classify_existing(
    artifacts: list[dict],
    recorded_ids: dict[str, str] | None = None,
) -> dict[str, dict]:
    """Map canonical studio keys to existing artifact records.

    Handles NotebookLM's post-generation classification quirks:
    - Completed or active (`in_progress`/`pending`) records take precedence over `failed` records
      regardless of input order; a failed record is retained only when no usable record exists.
    - Completed quizzes may report `type_id == 'flashcards'` (disambiguated by title or recorded ID).
    - Reports share `type_id == 'report'` (disambiguated by explicit title/type markers or recorded ID;
      unrecognized custom reports are NOT blindly mapped to `blog-post`).
    """
    found: dict[str, dict] = {}
    id_to_key = {art_id: k for k, art_id in (recorded_ids or {}).items() if art_id}

    for art in artifacts:
        art_id = str(art.get("id") or "")
        t_id = (art.get("type_id") or "").lower()
        t_label = (art.get("type") or "").lower()
        title = (art.get("title") or "").lower()

        if art_id and art_id in id_to_key:
            _select_artifact(found, id_to_key[art_id], art)
            continue

        if t_id == "audio":
            _select_artifact(found, "audio", art)
        elif t_id == "video":
            _select_artifact(found, "video", art)
        elif t_id == "infographic":
            _select_artifact(found, "infographic", art)
        elif t_id == "slide_deck":
            _select_artifact(found, "slide-deck", art)
        elif t_id == "mind_map":
            _select_artifact(found, "mind-map", art)
        elif t_id == "quiz":
            _select_artifact(found, "quiz", art)
        elif t_id == "flashcards":
            # NotebookLM studio_status / artifact list can classify completed quizzes as flashcards
            if "quiz" in title or "questionário" in title or "teste" in title:
                _select_artifact(found, "quiz", art)
            elif (
                "flashcard" in title
                or "cartões" in title
                or "cartoes" in title
                or "flashcards" not in found
                or (found["flashcards"].get("status") or "").lower()
                not in USABLE_STATUSES
            ):
                _select_artifact(found, "flashcards", art)
            else:
                _select_artifact(found, "quiz", art)
        elif t_id == "data_table":
            _select_artifact(found, "table-report", art)
        elif t_id == "report":
            if t_label == "briefing doc" or "briefing" in title:
                _select_artifact(found, "briefing-doc", art)
            elif (
                t_label == "study guide"
                or "guia de estudo" in title
                or "study guide" in title
            ):
                _select_artifact(found, "study-guide", art)
            elif (
                "comparativo técnico" in title
                or "tabela" in title
                or "comparison table" in title
            ):
                _select_artifact(found, "table-report", art)
            elif (
                t_label == "blog post"
                or "blog" in title
                or "na prática:" in title
                or "artigo" in title
            ):
                _select_artifact(found, "blog-post", art)
    for key, art_id in (recorded_ids or {}).items():
        preferred = next(
            (art for art in artifacts if str(art.get("id") or "") == str(art_id)),
            None,
        )
        if preferred and str(preferred.get("status") or "").lower() in USABLE_STATUSES:
            found[key] = preferred
    return found


def find_generated_artifacts(
    artifacts: list[dict], generated_ids: dict[str, str]
) -> dict[str, dict]:
    """Resolve this run's generated task IDs to their listed artifact rows."""
    artifacts_by_id = {str(art.get("id") or ""): art for art in artifacts}
    return {
        key: artifacts_by_id[art_id]
        for key, art_id in generated_ids.items()
        if art_id in artifacts_by_id
    }


def is_unsupported_data_table_error(out: dict | str) -> bool:
    """Return True only when data-table failed due to server rejecting type=9 as invalid argument."""
    if isinstance(out, dict):
        code = str(out.get("code") or "")
        msg = str(out.get("message") or "").lower()
        return code == "UNCONFIRMED_WRITE" and "invalid argument" in msg
    text = str(out).lower()
    return "unconfirmed_write" in text and "invalid argument" in text


def extract_created_id(out: dict | str) -> str:
    if isinstance(out, dict):
        return str(out.get("task_id") or out.get("id") or out.get("note_id") or "")
    return ""


def build_specs(nb: str, focus: str, lang: str) -> list[tuple[str, list[str]]]:
    return [
        (
            "audio",
            [
                "generate",
                "audio",
                "-n",
                nb,
                "--format",
                "deep-dive",
                "--length",
                "default",
                "--language",
                lang,
                f"Foque em: {focus}",
                "--json",
            ],
        ),
        (
            "video",
            [
                "generate",
                "video",
                "-n",
                nb,
                "--format",
                "explainer",
                "--style",
                "auto",
                "--language",
                lang,
                f"Explique visualmente: {focus}",
                "--json",
            ],
        ),
        (
            "infographic",
            [
                "generate",
                "infographic",
                "-n",
                nb,
                "--orientation",
                "landscape",
                "--detail",
                "detailed",
                "--language",
                lang,
                f"Visão geral comparativa e arquitetural sobre: {focus}",
                "--json",
            ],
        ),
        (
            "slide-deck",
            [
                "generate",
                "slide-deck",
                "-n",
                nb,
                "--format",
                "detailed",
                "--length",
                "default",
                "--language",
                lang,
                f"Apresentação técnica completa sobre: {focus}",
                "--json",
            ],
        ),
        (
            "briefing-doc",
            [
                "generate",
                "report",
                "-n",
                nb,
                "--format",
                "briefing-doc",
                "--language",
                lang,
                "--append",
                f"Responda em português brasileiro (pt-BR). Foque em: {focus}",
                "--json",
            ],
        ),
        (
            "study-guide",
            [
                "generate",
                "report",
                "-n",
                nb,
                "--format",
                "study-guide",
                "--language",
                lang,
                "--append",
                f"Responda em português brasileiro (pt-BR). Foque nos conceitos-chave, arquitetura e prática: {focus}",
                "--json",
            ],
        ),
        (
            "blog-post",
            [
                "generate",
                "report",
                "-n",
                nb,
                "--format",
                "blog-post",
                "--language",
                lang,
                "--append",
                f"Responda em português brasileiro (pt-BR). Inicie o título com 'Blog:' ou 'Na Prática:'. Artigo técnico sobre: {focus}",
                "--json",
            ],
        ),
        (
            "flashcards",
            [
                "generate",
                "flashcards",
                "-n",
                nb,
                "--difficulty",
                "medium",
                "--quantity",
                "standard",
                f"Em português brasileiro (pt-BR): conceitos-chave e arquitetura sobre {focus}.",
                "--json",
            ],
        ),
        (
            "quiz",
            [
                "generate",
                "quiz",
                "-n",
                nb,
                "--difficulty",
                "medium",
                "--quantity",
                "more",
                f"Em português brasileiro (pt-BR): perguntas técnicas e práticas sobre {focus}.",
                "--json",
            ],
        ),
        (
            "mind-map",
            [
                "generate",
                "mind-map",
                "-n",
                nb,
                "--language",
                lang,
                "--instructions",
                f"Mapa mental em português brasileiro (pt-BR) cobrindo: {focus}.",
                "--json",
            ],
        ),
        (
            "table-report",
            [
                "generate",
                "report",
                "-n",
                nb,
                "--format",
                "custom",
                "--language",
                lang,
                f"Crie uma Tabela de Dados comparativa completa em português brasileiro (pt-BR) estruturada em formato tabular Markdown (inicie o título com 'Comparativo Técnico:') sobre {focus}, incluindo colunas para Componente/Critério, Funcionalidades, Performance/Latência, UX, Vantagens e Limitações.",
                "--json",
            ],
        ),
    ]


def build_native_table_spec(nb: str, focus: str, lang: str) -> list[str]:
    return [
        "generate",
        "data-table",
        "-n",
        nb,
        "--language",
        lang,
        f"Tabela comparativa sobre {focus}",
        "--json",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", "--notebook", required=True, help="Notebook URL or UUID")
    parser.add_argument("-f", "--focus", required=True, help="1-2 sentence topic focus (in pt-BR)")
    parser.add_argument(
        "--persona-config",
        default="persona_config.json",
        help="Path to persona_config.json",
    )
    parser.add_argument("--lang", default="pt_BR", help="Output language code (default: pt_BR)")
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Seconds between CLI calls (default: 1.5)",
    )
    parser.add_argument(
        "--only",
        default="",
        help=f"Comma-separated subset of artifact keys ({','.join(SUPPORTED_KEYS)})",
    )
    parser.add_argument(
        "--try-native-table",
        action="store_true",
        help="Try native data-table before custom report",
    )
    parser.add_argument(
        "--no-wait-audio",
        action="store_true",
        help="Do not wait for audio overview to finish before dispatching video",
    )
    parser.add_argument(
        "--audio-wait-timeout",
        type=int,
        default=600,
        help="Max seconds to wait for audio before dispatching video (default: 600)",
    )
    parser.add_argument(
        "--ignore-fingerprint",
        action="store_true",
        help="Reuse existing artifacts even if recorded inputs changed",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate requested artifacts even if they already exist",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing",
    )
    args = parser.parse_args()

    nb = extract_notebook_id(args.notebook)
    focus = args.focus.strip()
    lang = args.lang

    # Comment 12: Validate --only keys up front
    only_set = {k.strip() for k in args.only.split(",") if k.strip()}
    unknown_keys = sorted(only_set - set(SUPPORTED_KEYS))
    if unknown_keys:
        print(
            f"ERROR: Unknown --only key(s): {', '.join(unknown_keys)}. "
            f"Supported keys: {', '.join(SUPPORTED_KEYS)}",
            file=sys.stderr,
        )
        return 2

    specs = build_specs(nb, focus, lang)
    target_keys = [k for k, _ in specs if not only_set or k in only_set]

    # 1. Load persona_config.json if available
    persona = DEFAULT_PERSONA
    resp_len = DEFAULT_RESPONSE_LENGTH
    cfg_path = Path(args.persona_config)
    if cfg_path.is_file():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        persona = cfg.get("persona") or persona
        resp_len = cfg.get("response_length") or resp_len

    cli = PacedCLI(delay=args.delay, dry_run=args.dry_run)
    failures: list[str] = []

    # Comment 2: Serialize concurrent runs targeting the same notebook
    with notebook_lock(nb) as state_dir:
        print(f"==> [1/4] Setting active context & configuring persona on {nb}...")
        rc_use, use_out = cli.run(["use", nb])
        if rc_use != 0:
            print(f"ERROR: 'notebooklm use' failed (rc={rc_use}): {use_out}", file=sys.stderr)
            return 1

        # Comment 4: Stop and fail if configure fails
        rc_cfg, cfg_out = cli.run(
            ["configure", "-n", nb, "--response-length", resp_len, "--persona", persona, "--json"]
        )
        if rc_cfg != 0:
            print(
                f"ERROR: 'notebooklm configure' failed (rc={rc_cfg}): {cfg_out}",
                file=sys.stderr,
            )
            return 1

        # Comment 11: Compute source/persona/focus inputs and compare per artifact.
        ok_fp, current_fp = fetch_sources_fingerprint(
            cli, nb, focus, lang, persona, resp_len
        )
        if not ok_fp:
            return 1
        native_table_command = (
            build_native_table_spec(nb, focus, lang) if args.try_native_table else None
        )
        current_artifact_fingerprints = {
            key: artifact_input_fingerprint(
                current_fp,
                key,
                cmd_args,
                native_table_command if key == "table-report" else None,
            )
            for key, cmd_args in specs
        }

        manifest = load_manifest(state_dir, nb)
        recorded_fp = manifest.get("fingerprint")
        if not isinstance(recorded_fp, str):
            recorded_fp = ""
        recorded_ids: dict[str, str] = (
            manifest.get("artifacts", {}) if isinstance(manifest.get("artifacts"), dict) else {}
        )
        raw_artifact_fingerprints = manifest.get("artifact_fingerprints", {})
        recorded_fingerprints: dict[str, str] = (
            {
                key: value
                for key, value in raw_artifact_fingerprints.items()
                if isinstance(key, str) and isinstance(value, str)
            }
            if isinstance(raw_artifact_fingerprints, dict)
            else {}
        )
        fingerprint_changed = bool(
            recorded_fp and recorded_fp != current_fp and not args.ignore_fingerprint
        )
        if fingerprint_changed:
            print(
                f"==> Notebook inputs or persona settings changed "
                f"(fingerprint {recorded_fp} -> {current_fp}); "
                "checking each requested artifact's recorded inputs..."
            )

        # Comment 1: Check artifact list return code and response shape
        print("==> [2/4] Inspecting existing Studio artifacts...")
        ok_list, existing_list = fetch_artifacts(cli, nb)
        if not ok_list:
            return 1
        existing_map = classify_existing(existing_list, recorded_ids=recorded_ids)

        print(f"==> [3/4] Dispatching Studio artifacts (pacing={args.delay}s)...")
        dispatched_audio_id: str | None = None
        audio_wait_required = False
        wants_video = "video" in target_keys
        existing_audio = existing_map.get("audio")
        if existing_audio and str(existing_audio.get("status") or "").lower() in (
            "in_progress",
            "pending",
        ):
            dispatched_audio_id = str(existing_audio.get("id") or "") or None
            audio_wait_required = True
        fingerprint_candidates: dict[str, str] = {}
        generated_keys: set[str] = set()
        generated_ids_by_key: dict[str, str] = {}

        for key, cmd_args in specs:
            if only_set and key not in only_set:
                continue

            prev = existing_map.get(key)
            current_artifact_fp = current_artifact_fingerprints[key]
            prev_fingerprint = recorded_fingerprints.get(key)
            artifact_stale = bool(
                prev
                and prev_fingerprint
                and prev_fingerprint != current_artifact_fp
                and not args.ignore_fingerprint
            )
            if artifact_stale:
                print(f"  [STALE] {key}: recorded inputs differ; regenerating...")
            if prev and not args.force and not artifact_stale:
                status = (prev.get("status") or "").lower()
                art_id = str(prev.get("id") or "")
                if status in USABLE_STATUSES:
                    print(f"  [SKIP] {key}: already {status} (id={art_id})")
                    if art_id:
                        recorded_ids[key] = art_id
                    if key == "audio" and status in ("in_progress", "pending") and wants_video:
                        dispatched_audio_id = art_id or None
                        audio_wait_required = True
                    continue
                if status == "failed" and art_id:
                    if (
                        key == "video"
                        and audio_wait_required
                        and not args.no_wait_audio
                    ):
                        if not wait_for_audio_completion(
                            cli,
                            nb,
                            dispatched_audio_id,
                            args.audio_wait_timeout,
                            "retrying video",
                        ):
                            failures.append("audio-wait-before-video")
                            continue
                        audio_wait_required = False
                    # Comment 8: Check retry result and fall back to fresh generation if retry fails
                    print(f"  [RETRY] {key}: retrying failed artifact {art_id}")
                    rc_retry, retry_out = cli.run(["artifact", "retry", art_id, "-n", nb, "--json"])
                    if rc_retry == 0:
                        recorded_ids[key] = art_id
                        if (
                            prev_fingerprint == current_artifact_fp
                            and not args.ignore_fingerprint
                        ):
                            fingerprint_candidates[key] = art_id
                        if key == "audio" and wants_video:
                            dispatched_audio_id = art_id
                            audio_wait_required = True
                        continue
                    print(
                        f"  [WARN] retry failed for {key} (rc={rc_retry}: {retry_out}); "
                        "falling back to fresh generation...",
                        file=sys.stderr,
                    )

            if key == "audio" and audio_wait_required:
                if not wait_for_audio_completion(
                    cli,
                    nb,
                    dispatched_audio_id,
                    args.audio_wait_timeout,
                    "starting replacement audio",
                ):
                    failures.append("audio-wait-before-audio")
                    continue
                audio_wait_required = False
                dispatched_audio_id = None

            if (
                key == "video"
                and audio_wait_required
                and not args.no_wait_audio
            ):
                if not wait_for_audio_completion(
                    cli,
                    nb,
                    dispatched_audio_id,
                    args.audio_wait_timeout,
                    "dispatching video",
                ):
                    failures.append("audio-wait-before-video")
                    continue
                audio_wait_required = False

            if key == "table-report" and args.try_native_table:
                # Comment 10: Only fall back to custom report on the unsupported-operation error
                assert native_table_command is not None
                rc_dt, dt_out = cli.run(native_table_command)
                if rc_dt == 0:
                    generated_keys.add(key)
                    created_id = extract_created_id(dt_out)
                    if created_id:
                        generated_ids_by_key[key] = created_id
                        recorded_ids[key] = created_id
                    print("  [OK] table-report (native data-table)")
                    continue
                if not is_unsupported_data_table_error(dt_out):
                    print(
                        f"  [ERR({rc_dt})] table-report (native data-table): {dt_out}",
                        file=sys.stderr,
                    )
                    failures.append(key)
                    continue
                print(
                    "  [FALLBACK] native data-table rejected (UNCONFIRMED_WRITE / invalid argument); "
                    "generating custom tabular report..."
                )

            if key == "audio" and wants_video:
                # Do not let a previous audio ID mask an accepted generation whose ID is missing.
                dispatched_audio_id = None
                audio_wait_required = True
            wait_inline = (
                key == "audio"
                and wants_video
                and not args.no_wait_audio
            )
            dispatch_args = cmd_args
            if wait_inline:
                # The CLI's --wait blocks on the generation task ID; artifact wait accepts artifact IDs.
                dispatch_args = [
                    *cmd_args,
                    "--wait",
                    "--timeout",
                    str(args.audio_wait_timeout),
                ]
            rc, out = cli.run(dispatch_args)
            if rc != 0 and not args.dry_run:
                if wait_inline:
                    # A timed-out --wait may leave a live server task; don't start duplicate audio.
                    print(
                        f"  [WARN] {key} generation/wait failed (rc={rc}: {out}); "
                        "not dispatching a second audio task; checking final status...",
                        file=sys.stderr,
                    )
                else:
                    # Comment 9: Bounded retry on immediate generation failure (paced by PacedCLI)
                    print(
                        f"  [WARN] {key} generation failed (rc={rc}: {out}); retrying once...",
                        file=sys.stderr,
                    )
                    rc, out = cli.run(dispatch_args)

            if rc == 0:
                created_id = extract_created_id(out)
                generated_keys.add(key)
                if created_id:
                    generated_ids_by_key[key] = created_id
                    recorded_ids[key] = created_id
                if key == "audio" and wants_video:
                    dispatched_audio_id = created_id or None
                    audio_wait_required = not wait_inline
                print(f"  [OK] {key}: {out if isinstance(out, dict) else str(out)[:120]}")
            else:
                print(
                    f"  [ERR({rc})] {key}: {out if isinstance(out, dict) else str(out)[:120]}",
                    file=sys.stderr,
                )
                failures.append(key)

        # Comment 9: Inspect final listing and retry any newly failed artifacts once
        print("==> [4/4] Fetching final Studio status...")
        ok_final, final_artifacts = fetch_artifacts(cli, nb)
        if not ok_final:
            return 1

        final_map = classify_existing(final_artifacts, recorded_ids=recorded_ids)
        generated_artifacts = find_generated_artifacts(final_artifacts, generated_ids_by_key)
        retried_in_final = False
        for key in target_keys:
            art = generated_artifacts.get(key) if key in generated_keys else final_map.get(key)
            if art and (art.get("status") or "").lower() == "failed" and art.get("id"):
                art_id = str(art["id"])
                print(f"  [FINAL-RETRY] {key}: retrying newly failed artifact {art_id}...")
                rc_fr, fr_out = cli.run(["artifact", "retry", art_id, "-n", nb, "--json"])
                retried_in_final = True
                if rc_fr != 0:
                    print(
                        f"  [ERR({rc_fr})] final retry failed for {key}: {fr_out}",
                        file=sys.stderr,
                    )
                    if key not in failures:
                        failures.append(key)
                elif (
                    not args.ignore_fingerprint
                    and art_id
                    and recorded_fingerprints.get(key) == current_artifact_fingerprints[key]
                ):
                    fingerprint_candidates[key] = art_id

        if retried_in_final:
            ok_final, final_artifacts = fetch_artifacts(cli, nb)
            if not ok_final:
                return 1
            final_map = classify_existing(final_artifacts, recorded_ids=recorded_ids)
            generated_artifacts = find_generated_artifacts(final_artifacts, generated_ids_by_key)

        for key in target_keys:
            art = generated_artifacts.get(key) if key in generated_keys else final_map.get(key)
            status = str(art.get("status") or "").lower() if art else ""
            art_id = str(art.get("id") or "") if art else ""
            if art and art_id and status in USABLE_STATUSES:
                recorded_ids[key] = art_id
                if key in generated_keys or fingerprint_candidates.get(key) == art_id:
                    recorded_fingerprints[key] = current_artifact_fingerprints[key]
                    failures = [failure for failure in failures if failure != key]
            if (
                not args.dry_run
                and (not art or status not in USABLE_STATUSES)
                and key not in failures
            ):
                failures.append(key)

        if not args.dry_run:
            save_manifest(
                state_dir,
                nb,
                {
                    "notebook_id": nb,
                    "fingerprint": current_fp,
                    "focus": focus,
                    "lang": lang,
                    "artifacts": recorded_ids,
                    "artifact_fingerprints": recorded_fingerprints,
                },
            )

        summary_payload = {
            "notebook_id": nb,
            "persona_status": "planned" if args.dry_run else "applied",
            "fingerprint": current_fp,
            "count": len(final_artifacts),
            "failures": failures,
            "artifacts": final_artifacts,
        }
        print(json.dumps(summary_payload, indent=2, ensure_ascii=False))

        # Comment 3: Return non-zero if any required command or artifact failed
        if failures:
            print(
                f"ERROR: Studio run completed with failed/unverified step(s): {', '.join(failures)}",
                file=sys.stderr,
            )
            return 1
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
