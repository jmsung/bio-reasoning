"""Human-readable optimization journal — one legible entry per loop iteration.

``trials.jsonl`` is terse and ``leaderboard.md`` only ranks; neither tells you
*whether the search is improving or random-walking*. The journal does: per
iteration it records the config tried, the single knob that changed versus the
running best, the result with its noise band (so a Δ can be read against noise),
accept/reject, and the best-so-far trajectory.

Pure and file-free at the core (``render_journal_entry``) so it is unit-testable;
``append_journal_entry`` is the thin file sink wired as the driver's ``on_record``
hook. Both take the *full running history* and render the entry for its last
record, using the earlier records for the running best, Δ, and trajectory.
"""

from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path

from bio_reasoning.trial_loop.types import TrialRecord, Variant

_BAND_RE = re.compile(r"band=([0-9]*\.?[0-9]+)")


def _mean(rec: TrialRecord) -> float:
    return float(rec.metrics.get("mean", float("nan")))


def _fmt(x: float) -> str:
    return "nan" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3f}"


def _template_hash(template: str) -> str:
    return hashlib.sha1(template.encode()).hexdigest()[:8]


def _prompt_label(v: Variant) -> str:
    if v.prompt_template is not None:
        return f"template#{_template_hash(v.prompt_template)}"
    return v.prompt


def _noise_band(rec: TrialRecord) -> float | None:
    """Recover the gate's measured noise band (max−min across split seeds).

    The gate persists it into the reflection string (``band=X.XXX``); that is the
    only place it survives on a ``TrialRecord``, so parse it back. ``None`` when
    absent (older records / a reflection without the tag)."""
    if rec.reflection:
        m = _BAND_RE.search(rec.reflection)
        if m:
            return float(m.group(1))
    return None


def _knob_diff(cand: Variant, best: Variant | None) -> str:
    """Describe which knob(s) differ between ``cand`` and the running-best variant."""
    if best is None:
        return "(first trial — vs initial baseline)"
    diffs: list[str] = []
    if _prompt_label(cand) != _prompt_label(best):
        diffs.append(f"prompt {_prompt_label(best)}→{_prompt_label(cand)}")
    if cand.n_few_shot != best.n_few_shot:
        diffs.append(f"few_shot {best.n_few_shot}→{cand.n_few_shot}")
    if cand.retrieval != best.retrieval:
        diffs.append(f"retrieval {best.retrieval}→{cand.retrieval}")
    if len(cand.seeds) != len(best.seeds):
        diffs.append(f"samples {len(best.seeds)}→{len(cand.seeds)}")
    if cand.tools != best.tools:
        diffs.append(f"tools {best.tools}→{cand.tools}")
    if cand.self_critique != best.self_critique:
        diffs.append(f"self_critique {best.self_critique}→{cand.self_critique}")
    return ", ".join(diffs) if diffs else "no knob change (same config as best)"


def _running_best(history: list[TrialRecord]) -> tuple[float, int]:
    """Return (best mean, 1-based iter) over ``history`` — nan ranked last."""
    best_mean, best_i = -math.inf, 0
    for i, rec in enumerate(history, start=1):
        m = _mean(rec)
        if not math.isnan(m) and m > best_mean:
            best_mean, best_i = m, i
    return best_mean, best_i


def render_journal_entry(history: list[TrialRecord], *, reason: str | None = None) -> str:
    """Render the human-readable journal entry for ``history[-1]``.

    Earlier records supply the running best (for the knob-diff and best-so-far),
    the Δ, and the trajectory. ``reason`` is an optional optimizer/mutation note
    shown next to the knob-diff; when the caller passes none it falls back to the
    variant's own ``reason`` (a reflective mutation attaches the *why* there), so a
    reflection-driven run logs its reasoning per generation."""
    if not history:
        raise ValueError("render_journal_entry() on empty history")

    n = len(history)
    rec = history[-1]
    v = rec.variant
    if reason is None:
        reason = v.reason
    m = rec.metrics
    prior = history[:-1]
    best_prior = max(
        prior, key=lambda r: (-math.inf if math.isnan(_mean(r)) else _mean(r)), default=None
    )

    mean = _mean(rec)
    band = _noise_band(rec)
    band_str = "n/a" if band is None else f"{band:.3f}"
    accepted = bool(m.get("accepted", 0.0))
    verdict = "ACCEPTED" if accepted else "REJECTED"

    delta = mean - float(m.get("baseline_mean", float("nan")))
    best_mean, best_i = _running_best(history)
    trajectory = " → ".join(_fmt(_mean(r)) for r in history)

    diff = _knob_diff(v, best_prior.variant if best_prior else None)
    diff_line = diff if reason is None else f"{diff} (reason: {reason})"

    lines = [
        f"iter {n} | config: prompt={_prompt_label(v)}, few_shot={v.n_few_shot}, "
        f"retrieval={v.retrieval}, samples={len(v.seeds)}",
        f"       | changed-vs-best: {diff_line}",
        f"       | result: mean {_fmt(mean)} ± {band_str}  "
        f"(de {_fmt(m.get('auroc_de', float('nan')))} / dir {_fmt(m.get('auroc_dir', float('nan')))})  "
        f"Δvs-best {delta:+.3f}  → {verdict}",
        f"       | best-so-far: {_fmt(best_mean)} (iter {best_i})   trajectory: [{trajectory}]",
    ]
    if v.prompt_template is not None:
        lines += [
            "",
            f"       prompt_template#{_template_hash(v.prompt_template)} (full text):",
            "       ```",
            v.prompt_template.strip(),
            "       ```",
        ]
    return "\n".join(lines)


_HEADER = (
    "# Optimization journal\n\n"
    "One entry per loop iteration: config tried, the knob changed vs the running best, "
    "result ± noise band, and the best-so-far trajectory. Read the trajectory to tell "
    "whether the search is climbing or random-walking; read `± band` to tell whether a "
    "Δ is real or inside noise.\n\n"
)


def append_journal_entry(
    path: Path, history: list[TrialRecord], *, reason: str | None = None
) -> None:
    """Append the entry for ``history[-1]`` to ``journal.md`` (creating it + header)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = _HEADER if not path.exists() else ""
    with path.open("a") as fh:
        fh.write(prefix + render_journal_entry(history, reason=reason) + "\n\n")
