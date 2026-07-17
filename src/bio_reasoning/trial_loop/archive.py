"""Persist trial-loop results: ``trials.jsonl`` history, a leaderboard, best variant.

The archive is how a loop run is inspected and resumed: every :class:`TrialRecord`
is a JSONL line, the leaderboard ranks variants by OOD-val mean, and the best
variant's config is written out for the next iteration to build on.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict
from pathlib import Path

from bio_reasoning.trial_loop.reflect import best_trial
from bio_reasoning.trial_loop.types import TrialRecord

PRIOR_FLOOR = 0.533


def write_trials(path: Path, records: list[TrialRecord]) -> None:
    """Write ``records`` as JSONL (one TrialRecord per line), overwriting ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(r.to_json() + "\n" for r in records))


def load_trials(path: Path) -> list[TrialRecord]:
    """Read a ``trials.jsonl`` file; empty list if it does not exist."""
    if not Path(path).exists():
        return []
    return [
        TrialRecord.from_json(line) for line in Path(path).read_text().splitlines() if line.strip()
    ]


def _mean(rec: TrialRecord) -> float:
    return float(rec.metrics.get("mean", float("nan")))


def leaderboard(history: list[TrialRecord]) -> list[TrialRecord]:
    """Return trials sorted by OOD-val mean, descending (nan ranked last)."""
    return sorted(
        history, key=lambda r: (-math.inf if math.isnan(_mean(r)) else _mean(r)), reverse=True
    )


def render_leaderboard(history: list[TrialRecord]) -> str:
    """Render the leaderboard as a markdown table, best variant first."""
    board = leaderboard(history)
    header = (
        "| rank | variant | mean | auroc_de | auroc_dir | n_val | cost_usd |\n"
        "|---|---|---|---|---|---|---|"
    )
    rows = []
    for i, r in enumerate(board, start=1):
        m = r.metrics
        cost = "" if r.cost_usd is None else f"{r.cost_usd:.4f}"
        rows.append(
            f"| {i} | {r.variant.id} | {_mean(r):.3f} | {m.get('auroc_de', float('nan')):.3f} "
            f"| {m.get('auroc_dir', float('nan')):.3f} | {m.get('n_val', 0)} | {cost} |"
        )
    note = ""
    if board:
        top = _mean(board[0])
        verdict = "BEATS" if top > PRIOR_FLOOR else "below"
        note = f"\n\nBest OOD-val mean **{top:.3f}** — {verdict} the {PRIOR_FLOOR} prior floor."
    return header + "\n" + "\n".join(rows) + note


def compare_agentic_vs_prompt(history: list[TrialRecord]) -> dict[str, object]:
    """Split ``history`` into agentic (``variant.tools is not None``) vs prompt-only.

    Returns ``{agentic_best, prompt_best, delta}`` where each ``*_best`` is that arm's
    top TrialRecord by OOD-val mean (``None`` if the arm is empty) and ``delta`` is
    ``agentic_best.mean − prompt_best.mean`` (``None`` if either arm is missing) — the
    honest A/B: does giving the agent real tools beat the prompt-only baseline?
    """
    agentic = [r for r in history if r.variant.tools is not None]
    prompt = [r for r in history if r.variant.tools is None]
    a_best = best_trial(agentic) if agentic else None
    p_best = best_trial(prompt) if prompt else None
    delta = None if a_best is None or p_best is None else _mean(a_best) - _mean(p_best)
    return {"agentic_best": a_best, "prompt_best": p_best, "delta": delta}


def render_agentic_vs_prompt(history: list[TrialRecord]) -> str:
    """Render the agentic-vs-prompt-only A/B as a short markdown block."""
    cmp = compare_agentic_vs_prompt(history)

    def _fmt(rec: TrialRecord | None) -> str:
        return "—" if rec is None else f"{rec.variant.id} ({_mean(rec):.3f})"

    lines = [
        "## Agentic vs prompt-only (dual-OOD mean AUROC)",
        "",
        f"- prompt-only best: {_fmt(cmp['prompt_best'])}",  # type: ignore[arg-type]
        f"- agentic best: {_fmt(cmp['agentic_best'])}",  # type: ignore[arg-type]
    ]
    delta = cmp["delta"]
    lines.append(
        "- delta: — (one arm missing)"
        if delta is None
        else f"- delta (agentic − prompt): {delta:+.3f}"
    )
    return "\n".join(lines)


def archive(output_dir: Path, history: list[TrialRecord]) -> dict[str, Path]:
    """Write ``leaderboard.md`` and ``best_variant.json`` for ``history``.

    Returns the paths written. ``trials.jsonl`` is appended by the runner; this
    refreshes the derived views from the full history.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    lb_path = output_dir / "leaderboard.md"
    lb_path.write_text(render_leaderboard(history) + "\n")

    best_path = output_dir / "best_variant.json"
    best_path.write_text(json.dumps(asdict(best_trial(history).variant), indent=2) + "\n")

    return {"leaderboard": lb_path, "best_variant": best_path}
