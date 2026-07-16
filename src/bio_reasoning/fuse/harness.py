"""Rank-fusion harness + CFA diversity gate for DE score channels.

Every candidate DE signal (CollecTRI TF-regulon, STRING coupling, the current
model score, …) is a *channel*: a 1-D array of per-row scores where higher =
more likely differentially expressed. Channels live on incomparable scales, so
they are combined by **rank**, not by value — :func:`fuse` maps each channel to
average-rank in ``[0, 1]`` and takes a (weighted) mean. Rank fusion is
scale-free, order-preserving within each channel, and deterministic.

A new channel only helps if it is both *strong* and *different*. The **CFA**
(Correlation-Filtered Admission) gate, :func:`cfa_gate`, admits a candidate iff
its standalone DE-AUROC clears ``min_auroc`` **and** its Spearman correlation
with the current fused score stays under ``max_corr`` — rejecting a channel that
merely re-states signal already in the fusion before it costs a Kaggle
submission.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from scipy.stats import rankdata, spearmanr
from sklearn.metrics import roc_auc_score


def rank_normalize(scores: Sequence[float]) -> np.ndarray:
    """Map ``scores`` to average-rank in ``[0, 1]`` (ties share a rank).

    Order-preserving and scale-free: the returned value is a monotone function
    of the input, so ranking is preserved. A single element maps to ``0.0``.
    """
    arr = np.asarray(scores, dtype=float)
    n = arr.shape[0]
    if n == 0:
        return np.empty(0, dtype=float)
    if n == 1:
        return np.zeros(1, dtype=float)
    r = rankdata(arr, method="average")  # 1..n, average for ties
    return (r - 1.0) / (n - 1.0)


def fuse(
    channels: Mapping[str, Sequence[float]],
    weights: Mapping[str, float] | None = None,
) -> np.ndarray:
    """Rank-fuse named score ``channels`` into one score in ``[0, 1]``.

    Each channel is rank-normalized (:func:`rank_normalize`) then combined as a
    weighted mean. ``weights`` defaults to equal weight per channel; missing
    keys default to ``1.0``. Deterministic and order-preserving in every
    channel. Raises ``ValueError`` on an empty mapping or unequal channel
    lengths.
    """
    if not channels:
        raise ValueError("fuse() needs at least one channel")
    lengths = {len(np.asarray(v)) for v in channels.values()}
    if len(lengths) != 1:
        raise ValueError(f"channels have unequal lengths: {sorted(lengths)}")

    w = {name: 1.0 for name in channels}
    if weights:
        w.update(weights)

    n = lengths.pop()
    acc = np.zeros(n, dtype=float)
    total = 0.0
    for name, scores in channels.items():
        acc += w[name] * rank_normalize(scores)
        total += w[name]
    if total == 0:
        raise ValueError("channel weights sum to zero")
    return acc / total


@dataclass
class CFAResult:
    """Verdict from :func:`cfa_gate`.

    ``admit`` is the decision; ``de_auroc`` is the candidate's standalone
    none-vs-DE AUROC; ``max_spearman`` is ``|Spearman|`` against the current
    fused score (``0.0`` when there is no fusion yet); ``reason`` names the
    failing criterion (or ``"admit"``).
    """

    admit: bool
    de_auroc: float
    max_spearman: float
    reason: str


def cfa_gate(
    candidate: Sequence[float],
    current_fused: Sequence[float] | None,
    de_true: Sequence[int],
    *,
    min_auroc: float = 0.55,
    max_corr: float = 0.7,
) -> CFAResult:
    """Decide whether to admit ``candidate`` into the fusion.

    Admits iff the candidate is **strong** — standalone DE-AUROC (against 0/1
    ``de_true``) ``>= min_auroc`` — **and diverse** — ``|Spearman|`` vs
    ``current_fused`` ``<= max_corr``. ``current_fused=None`` means the first
    channel, so the correlation test is skipped (``max_spearman = 0``).
    """
    cand = np.asarray(candidate, dtype=float)
    y = np.asarray(de_true).astype(int)
    de_auroc = float(roc_auc_score(y, cand)) if len(set(y.tolist())) > 1 else float("nan")

    if current_fused is None:
        corr = 0.0
    else:
        rho = spearmanr(cand, np.asarray(current_fused, dtype=float)).statistic
        corr = 0.0 if np.isnan(rho) else abs(float(rho))

    if not (de_auroc >= min_auroc):
        reason = f"weak: de_auroc={de_auroc:.3f} < {min_auroc}"
    elif corr > max_corr:
        reason = f"redundant: |spearman|={corr:.3f} > {max_corr}"
    else:
        reason = "admit"
    return CFAResult(admit=reason == "admit", de_auroc=de_auroc, max_spearman=corr, reason=reason)
