"""Rank-fusion of DE/direction channels + a CFA (conditionally-add-features) gate.

A *channel* contributes a DE score (``s_de``, higher = more likely differentially
expressed) and/or a direction score (``r`` = P(up)) per row, with ``NaN`` marking
rows the channel does not cover (e.g. a TF-regulon channel covers only TF perts).

``fuse`` rank-normalizes each channel's contributions to ``(0, 1)`` and averages
them per row (ignoring uncovered rows), then recombines into the ``(up, down)``
pair the Track A scorer consumes::

    up   = s_de_fused * r_fused
    down = s_de_fused * (1 - r_fused)

Rank (not value) fusion is deliberate: the metric is AUROC, which only sees
ordering, so mixing a calibrated base channel with a raw new one is safe. A row
no channel covers falls back to the neutral ``0.5``.

``cfa_gate`` decides whether a new channel earns a place in the fusion: it must be
individually predictive (standalone DE-AUROC ≥ ``min_auroc``) AND add information
(``|Spearman r|`` vs the current fused ``s_de`` ≤ ``max_abs_corr``) — validated on
the OOD-val partition before spending an LB submission.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import rankdata, spearmanr
from sklearn.metrics import roc_auc_score


@dataclass
class Channel:
    """One signal source. ``s_de`` and/or ``r`` are per-row arrays; ``NaN`` = uncovered."""

    name: str
    s_de: np.ndarray | None = None
    r: np.ndarray | None = None

    def __len__(self) -> int:
        arr = self.s_de if self.s_de is not None else self.r
        if arr is None:
            raise ValueError(f"channel {self.name!r} carries neither s_de nor r")
        return len(arr)


def _rank_norm(x) -> np.ndarray:
    """Rank-normalize finite entries into ``(0, 1)``; ``NaN`` stays ``NaN``.

    Uses ``rank / (m + 1)`` over the ``m`` finite values (average ranks for ties),
    so a lone finite value maps to the neutral ``0.5`` and the open interval avoids
    hard ``0``/``1`` endpoints.
    """
    x = np.asarray(x, dtype=float)
    out = np.full(x.shape, np.nan)
    finite = np.isfinite(x)
    m = int(finite.sum())
    if m == 0:
        return out
    out[finite] = rankdata(x[finite]) / (m + 1)
    return out


def _weighted_nanmean(stack: np.ndarray, weights) -> np.ndarray:
    """Per-column weighted mean of a ``(k, n)`` stack, skipping ``NaN``; empty → 0.5."""
    w = np.asarray(weights, dtype=float)[:, None]
    mask = np.isfinite(stack)
    wsum = np.where(mask, w, 0.0).sum(axis=0)
    vals = np.where(mask, stack * w, 0.0).sum(axis=0)
    out = np.full(stack.shape[1], 0.5)
    nz = wsum > 0
    out[nz] = vals[nz] / wsum[nz]
    return out


def fuse(channels: list[Channel], weights=None) -> tuple[np.ndarray, np.ndarray]:
    """Rank-fuse channels into ``(up, down)`` predictions aligned to the rows.

    Each channel's ``s_de`` and ``r`` are rank-normalized then averaged (weighted,
    ignoring uncovered rows). Rows/buses no channel covers default to ``0.5``.
    """
    if not channels:
        raise ValueError("fuse() needs at least one channel")
    n = len(channels[0])
    if weights is None:
        weights = [1.0] * len(channels)

    def _bus(attr: str) -> np.ndarray:
        stack, w = [], []
        for ch, cw in zip(channels, weights, strict=True):
            arr = getattr(ch, attr)
            if arr is not None:
                stack.append(_rank_norm(arr))
                w.append(cw)
        if not stack:
            return np.full(n, 0.5)
        return _weighted_nanmean(np.vstack(stack), w)

    s_de_fused = _bus("s_de")
    r_fused = _bus("r")
    up = s_de_fused * r_fused
    down = s_de_fused * (1.0 - r_fused)
    return up, down


def cfa_gate(
    candidate_s_de,
    current_s_de,
    de_true,
    *,
    min_auroc: float = 0.55,
    max_abs_corr: float = 0.5,
) -> tuple[bool, dict]:
    """Decide whether a candidate DE channel is predictive AND diverse enough to add.

    Scores the candidate on the rows it covers (finite ``candidate_s_de``): it passes
    iff standalone DE-AUROC ≥ ``min_auroc`` and ``|Spearman r|`` against the current
    fused ``s_de`` ≤ ``max_abs_corr``. Returns ``(passed, {auroc, corr, n_covered})``;
    ``corr`` is the absolute Spearman coefficient.
    """
    cand = np.asarray(candidate_s_de, dtype=float)
    cur = np.asarray(current_s_de, dtype=float)
    de = np.asarray(de_true).astype(int)

    cov = np.isfinite(cand)
    n_cov = int(cov.sum())
    stats = {"auroc": float("nan"), "corr": float("nan"), "n_covered": n_cov}
    if n_cov < 2 or len(set(de[cov].tolist())) < 2:
        return False, stats

    stats["auroc"] = float(roc_auc_score(de[cov], cand[cov]))
    both = cov & np.isfinite(cur)
    if int(both.sum()) >= 2:
        rho = spearmanr(cand[both], cur[both])[0]
        stats["corr"] = float(abs(rho)) if np.isfinite(rho) else 0.0
    else:
        stats["corr"] = 0.0

    passed = stats["auroc"] >= min_auroc and stats["corr"] <= max_abs_corr
    return passed, stats
