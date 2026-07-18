"""DE-learnability ceiling oracle — leakage-allowed features that UPPER-BOUND AUROC_de.

The go/no-go gate on the whole DE bet. Five pair-interaction DE channels and every
marginal proxy have scored at chance on the dual-OOD split (see the error-structure
EDA + `direction_channels`), so before engineering another DE channel this asks the
prior question: *is DE learnable at all from gene/pert identity?*

To answer it we deliberately CROSS the leak-free split boundary and give a head the
one thing an honest model never gets — each gene's and pert's true DE propensity,
computed from the full dataset (val included). This is an **oracle**: it can only do
better than any leak-free model, so its AUROC_de is a hard upper bound. ~0.50 ⇒ DE is
unlearnable by design (identity carries no transferable DE signal); >>0.50 ⇒ real
headroom exists and the per-feature ablation names which leaked feature carries it.

Marginal, never per-pair: the per-gene / per-pert DE-rate is **leave-one-out** (the
row's own label is excluded), so the score measures whether a gene/pert's OTHER pairs
predict a held-out pair — genuine marginal propensity — not the degenerate per-pair
label leakage (which would trivially give AUROC 1.0 for any singleton). These features
are ORACLE-ONLY: they are never built into a submission frame.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from bio_reasoning.eval.split import holdout_split

# Column order of the matrix returned by ``oracle_de_features``.
ORACLE_FEATURES: tuple[str, ...] = ("gene_de_rate", "pert_de_rate", "gene_count", "pert_count")


def group_rate_loo(keys: Sequence[str], de: Sequence[int], prior: float) -> np.ndarray:
    """Leave-one-out per-group DE-rate: each row's rate over its group's OTHER rows.

    For row ``i`` in group ``g``: ``(sum(de in g) - de[i]) / (count(g) - 1)``. A group
    of size 1 has no other rows, so it falls back to ``prior`` (the global DE-rate) —
    never its own label. Excluding self is what makes this a *marginal* propensity
    signal rather than per-pair label leakage.
    """
    key_arr = np.asarray(keys)
    de_arr = np.asarray(de, dtype=float)
    out = np.empty(len(de_arr), dtype=float)
    # Group by key; within each group compute the LOO mean in O(group size).
    order = np.argsort(key_arr, kind="stable")
    for start, stop in _contiguous_runs(key_arr[order]):
        idx = order[start:stop]
        n = len(idx)
        if n == 1:
            out[idx[0]] = prior
            continue
        total = de_arr[idx].sum()
        out[idx] = (total - de_arr[idx]) / (n - 1)
    return out


def _contiguous_runs(sorted_keys: np.ndarray):
    """Yield ``(start, stop)`` index spans of equal consecutive values."""
    n = len(sorted_keys)
    start = 0
    for i in range(1, n + 1):
        if i == n or sorted_keys[i] != sorted_keys[start]:
            yield start, i
            start = i


def marginal_rate(
    all_keys: Sequence[str], train_keys: Sequence[str], train_de: Sequence[int], prior: float
) -> np.ndarray:
    """Per-key DE-rate learned from TRAIN rows only, mapped onto ``all_keys``.

    A key absent from train (e.g. a dual-OOD held-out gene/pert) scores ``prior`` — it
    was never observed, so its propensity is genuinely unknown. This is the *honest*,
    transferable encoding: no val label ever informs a val row's own feature.
    """
    rate = pd.Series(np.asarray(train_de, dtype=float)).groupby(np.asarray(train_keys)).mean()
    lookup = rate.to_dict()
    return np.array([lookup.get(str(k), prior) for k in all_keys], dtype=float)


def oracle_de_features(
    df: pd.DataFrame, rate_train_idx: np.ndarray | None = None, prior: float | None = None
) -> np.ndarray:
    """Per-row oracle features → an ``(n, len(ORACLE_FEATURES))`` matrix.

    Columns (see ``ORACLE_FEATURES``):
      * ``gene_de_rate`` / ``pert_de_rate`` — marginal DE propensity. Two modes:
          - ``rate_train_idx=None`` (LEAKED): leave-one-out over the FULL frame (val
            included). This is the intentional leakage — but on a dual-OOD split it
            leaks each val row's label into its gene/pert-mates, so it is NOT
            achievable at test time (test identities are unseen). Use only to expose
            the leakage ceiling.
          - ``rate_train_idx=<train rows>`` (HONEST): rate learned from train only;
            an unseen (held-out) identity → ``prior``. The transferable bound.
      * ``gene_count`` / ``pert_count`` — full multiplicity of the gene/pert. A
        label-free structural stat, available for unseen identities → transferable.

    ORACLE-ONLY — never built into a submission frame.
    """
    de = (df["label"].to_numpy() != "none").astype(int)
    if prior is None:
        prior = float(de.mean())
    gene = df["gene"].astype(str).to_numpy()
    pert = df["pert"].astype(str).to_numpy()
    if rate_train_idx is None:
        gene_rate = group_rate_loo(gene, de, prior)
        pert_rate = group_rate_loo(pert, de, prior)
    else:
        gene_rate = marginal_rate(gene, gene[rate_train_idx], de[rate_train_idx], prior)
        pert_rate = marginal_rate(pert, pert[rate_train_idx], de[rate_train_idx], prior)
    gene_count = pd.Series(gene).map(pd.Series(gene).value_counts()).to_numpy(dtype=float)
    pert_count = pd.Series(pert).map(pd.Series(pert).value_counts()).to_numpy(dtype=float)
    return np.column_stack([gene_rate, pert_rate, gene_count, pert_count])


def de_auroc(de_true: np.ndarray, score: np.ndarray) -> float:
    """AUROC_de = rank none-vs-DE by ``score`` — the same quantity as ``evaluate``.

    Returns ``nan`` when the fold is single-class (no rank to score), never a fake
    number, so a degenerate fold can't masquerade as a real bound.
    """
    de_true = np.asarray(de_true)
    if len(set(de_true.tolist())) < 2:
        return float("nan")
    return float(roc_auc_score(de_true, np.asarray(score, dtype=float)))


def _fit_head_auroc(X, de, train_idx, val_idx) -> float:
    """Standardized logistic head fit on train rows, scored AUROC_de on val rows."""
    if len(set(de[train_idx].tolist())) < 2:
        return float("nan")
    head = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    head.fit(X[train_idx], de[train_idx])
    proba = head.predict_proba(X[val_idx])[:, 1]
    return de_auroc(de[val_idx], proba)


def de_ceiling_probe(
    df: pd.DataFrame,
    seeds: Sequence[int] = (0, 1, 2),
    pert_frac: float = 0.4,
    gene_frac: float = 0.4,
) -> dict[str, tuple[float, float]]:
    """Upper-bound AUROC_de on the dual-OOD val split — honest transfer vs leaked ceiling.

    For each split ``seed`` the val partition is scored by AUROC_de under two oracles:

    * **Honest / transferable** — per-gene/pert DE-rate learned from TRAIN only (unseen
      val identity → prior), plus label-free structural counts. Each feature is scored
      alone (the ablation) and combined by a ``fitted_head``. This is the real upper
      bound: nothing here uses a val row's own label. On a dual-OOD split every val
      identity is unseen, so the rate channels collapse to the prior (≈0.50) *by
      construction* — that collapse IS the finding (identity does not transfer).
    * **Leaked ceiling** (``leaked_head``) — the same head over FULL-frame leave-one-out
      rates, which leak each val label into its gene/pert-mates. Reported ONLY to expose
      how large a mirage that leakage creates; it is unachievable at test time.

    Returns ``{channel: (mean, std)}`` across seeds for the honest channels + ``fitted_head``
    + ``leaked_head``. The multi-seed spread is load-bearing: a feature that helps only by
    small-group noise (gene multiplicity is often ~2 here) shows as ≈0.50 with wide
    variance, not a stable lift. A ceiling, never a submittable model.
    """
    de = (df["label"].to_numpy() != "none").astype(int)
    X_leaked = oracle_de_features(df)  # full-LOO, leaked
    channels = [*ORACLE_FEATURES, "fitted_head", "leaked_head"]
    scores: dict[str, list[float]] = {c: [] for c in channels}

    for s in seeds:
        train_idx, val_idx = holdout_split(df, seed=s, pert_frac=pert_frac, gene_frac=gene_frac)
        if len(val_idx) == 0 or len(train_idx) == 0:
            continue
        de_val = de[val_idx]
        X_honest = oracle_de_features(df, rate_train_idx=train_idx)  # train-derived, honest
        for j, feat in enumerate(ORACLE_FEATURES):
            scores[feat].append(de_auroc(de_val, X_honest[val_idx, j]))
        scores["fitted_head"].append(_fit_head_auroc(X_honest, de, train_idx, val_idx))
        scores["leaked_head"].append(_fit_head_auroc(X_leaked, de, train_idx, val_idx))

    return {
        c: (float(np.nanmean(v)), float(np.nanstd(v))) if v else (float("nan"), 0.0)
        for c, v in scores.items()
    }
