"""Reflection + proposal for the trial-loop.

``reflect`` turns the trial history into a compact, human/LLM-readable summary of
each variant's OOD-val mean and its delta versus the running best — the context a
proposer uses to pick the next variant. A ``Proposer`` is any
``(reflection, history) -> Variant | None`` callable; ``make_grid_proposer`` is the
deterministic default (walk an untried candidate list, ``None`` when exhausted). An
LLM-backed proposer implements the same signature and is wired at run time.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from bio_reasoning.trial_loop.types import TrialRecord, Variant

# propose(reflection, history) -> next Variant to try, or None when converged.
Proposer = Callable[[str, list[TrialRecord]], "Variant | None"]


def _mean(rec: TrialRecord) -> float:
    return float(rec.metrics.get("mean", float("nan")))


def best_trial(history: list[TrialRecord]) -> TrialRecord:
    """Return the trial with the highest OOD-val mean (nan treated as -inf)."""
    if not history:
        raise ValueError("best_trial() on empty history")
    return max(history, key=lambda r: (-math.inf if math.isnan(_mean(r)) else _mean(r)))


def reflect(history: list[TrialRecord]) -> str:
    """Summarize trials so far: per-trial mean + delta vs the running best."""
    if not history:
        return "No trials yet."
    lines = []
    running_best = -math.inf
    for i, rec in enumerate(history):
        m = _mean(rec)
        delta = "" if math.isinf(running_best) else f" (Δ {m - running_best:+.3f} vs best)"
        lines.append(f"trial {i}: variant={rec.variant.id} mean={m:.3f}{delta}")
        if not math.isnan(m) and m > running_best:
            running_best = m
    b = best_trial(history)
    lines.append(f"best: variant={b.variant.id} mean={_mean(b):.3f}")
    return "\n".join(lines)


def make_grid_proposer(candidates: list[Variant]) -> Proposer:
    """Proposer that yields the next candidate (by ``id``) not yet in history.

    Returns ``None`` once every candidate has been tried — the loop's stop signal.
    The ``reflection`` argument is ignored here but is part of the signature so an
    LLM-backed proposer can use it in its place.
    """

    def _propose(reflection: str, history: list[TrialRecord]) -> Variant | None:
        tried = {r.variant.id for r in history}
        for v in candidates:
            if v.id not in tried:
                return v
        return None

    return _propose
