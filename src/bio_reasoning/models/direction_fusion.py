"""CFA-gate + rank-fuse multiple DIRECTION channels into one (up, down) prediction.

Three direction channels exist (GO two-stage, STRING-neighbour retrieval, LLM gene
embeddings); each supplies a per-row ``r`` = P(up). This module admits a candidate
only if its direction is predictive AND diverse, then rank-fuses the survivors with
the model's direction via :func:`~bio_reasoning.models.fuse.fuse`, keeping the
model's DE score unchanged (DE is the pinned axis).

The gate reuses the target-agnostic :func:`~bio_reasoning.models.fuse.cfa_gate`: on
DE-positive rows, a channel's ``r`` is scored against the ``is_up`` target
(DIR-AUROC) and against the current model direction (diversity). This is the
substrate the meta-loop bandit selects channels over.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from bio_reasoning.models.fuse import Channel, cfa_gate, fuse


def fuse_direction_channels(
    model_s_de,
    model_r,
    candidates: Sequence[tuple[str, np.ndarray]],
    labels,
    *,
    min_auroc: float = 0.55,
    max_abs_corr: float = 0.9,
) -> tuple[np.ndarray, np.ndarray, list[tuple[str, bool, dict]]]:
    """Gate + rank-fuse direction ``candidates`` with the model direction.

    ``candidates`` is ``[(name, r), ...]`` where ``r`` is P(up) per row (``NaN`` =
    uncovered). A candidate is admitted iff, on DE-positive rows, its ``r`` predicts
    up-vs-down (DIR-AUROC ≥ ``min_auroc``) AND is diverse from ``model_r``
    (``|Spearman|`` ≤ ``max_abs_corr``). Admitted channels' ``r`` are rank-fused with
    ``model_r``; the DE score stays ``model_s_de``. Returns ``(up, down, decisions)``
    where ``decisions`` is ``[(name, passed, stats), ...]``.
    """
    labels = np.asarray(labels)
    model_r = np.asarray(model_r, dtype=float)
    de = labels != "none"
    is_up = (labels[de] == "up").astype(int)

    decisions: list[tuple[str, bool, dict]] = []
    admitted: list[Channel] = []
    for name, r in candidates:
        r = np.asarray(r, dtype=float)
        passed, stats = cfa_gate(
            r[de], model_r[de], is_up, min_auroc=min_auroc, max_abs_corr=max_abs_corr
        )
        decisions.append((name, bool(passed), stats))
        if passed:
            # Gate scores direction on DE rows only, but fuse the FULL r: on non-DE rows
            # the model's low s_de damps `up/down = s_de·r`, so their direction barely counts.
            admitted.append(Channel(name, s_de=None, r=r))

    channels = [Channel("model", s_de=np.asarray(model_s_de, dtype=float), r=model_r), *admitted]
    up, down = fuse(channels)
    return up, down, decisions
