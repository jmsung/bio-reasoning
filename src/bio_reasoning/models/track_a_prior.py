"""Track A evidence-grounded prior baseline (no LLM).

Joo's proposal (PR #8, `docs/track-a-approach.md`): default every pair to low
DE-confidence and become confident only where prior biology supports it, using
the perturbation's *functional* category (never gene identity — test perts are
disjoint). Emits graded ``prediction_up`` / ``prediction_down`` as the metric
requires (`kaggle_metric_track_a.py`).

Per-category priors (hypothesis-grade, from `docs/track-a-eda.md`):
- direction ``u`` = P(up | DE): housekeeping skews up, immune/myeloid skews down.
- DE-confidence ``d``: raised for housekeeping (broad, conserved effect),
  moderate for immune, low default otherwise.

``prediction_up = d * u`` and ``prediction_down = d * (1 - u)``, so
``up + down = d`` (the DE score) and ``up / (up + down) = u`` (the DIR score).
"""

from __future__ import annotations

import numpy as np

# (P(up|DE), DE-confidence) per perturbation category.
PRIORS: dict[str, tuple[float, float]] = {
    "housekeeping": (0.70, 0.65),
    "immune": (0.40, 0.55),
    "other": (0.55, 0.45),
}


def predict(pert_symbols, categories: dict[str, str]) -> tuple[np.ndarray, np.ndarray]:
    """Return (pred_up, pred_down) arrays aligned to ``pert_symbols``."""
    up = np.empty(len(pert_symbols))
    down = np.empty(len(pert_symbols))
    for i, sym in enumerate(pert_symbols):
        u, d = PRIORS[categories.get(sym, "other")]
        up[i] = d * u
        down[i] = d * (1.0 - u)
    return up, down
