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


def oracle_de_features(df: pd.DataFrame, prior: float | None = None) -> np.ndarray:
    """Per-row leakage-allowed oracle features → an ``(n, len(ORACLE_FEATURES))`` matrix.

    Columns (see ``ORACLE_FEATURES``):
      * ``gene_de_rate`` / ``pert_de_rate`` — leave-one-out marginal DE propensity
        (self excluded; singleton → ``prior``). Computed over the FULL frame (val
        included) — this is the intentional leakage that makes the bound an oracle.
      * ``gene_count`` / ``pert_count`` — full multiplicity of the gene/pert (a
        marginal stat: how well its rate is estimated).

    ``prior`` defaults to the full-frame DE-rate. ORACLE-ONLY — never a submission path.
    """
    de = (df["label"].to_numpy() != "none").astype(int)
    if prior is None:
        prior = float(de.mean())
    gene = df["gene"].astype(str).to_numpy()
    pert = df["pert"].astype(str).to_numpy()
    gene_rate = group_rate_loo(gene, de, prior)
    pert_rate = group_rate_loo(pert, de, prior)
    gene_count = pd.Series(gene).map(pd.Series(gene).value_counts()).to_numpy(dtype=float)
    pert_count = pd.Series(pert).map(pd.Series(pert).value_counts()).to_numpy(dtype=float)
    return np.column_stack([gene_rate, pert_rate, gene_count, pert_count])
