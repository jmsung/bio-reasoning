"""Leak-free cross-validation splits for Track A/B.

The real test set shares **zero** perturbations and **zero** target genes with
train (see `docs/track-a-eda.md`). Random-row CV leaks both axes and inflates
local scores. `doubly_disjoint_folds` mirrors the real split: every evaluation
row has a perturbation **and** a gene that are absent from its training fold.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd


def _group(name: str, seed: int, k: int) -> int:
    """Deterministic 0..k-1 bucket for a name (stable across runs/machines)."""
    h = hashlib.md5(f"{seed}:{name}".encode()).hexdigest()
    return int(h, 16) % k


def _unit(name: str, seed: int) -> float:
    """Deterministic value in [0, 1) for a name (stable across runs/machines)."""
    h = hashlib.md5(f"{seed}:{name}".encode()).hexdigest()
    return (int(h, 16) % 10_000) / 10_000.0


def holdout_split(
    df: pd.DataFrame,
    seed: int = 0,
    pert_frac: float = 0.4,
    gene_frac: float = 0.4,
    pert_col: str = "pert",
    gene_col: str = "gene",
) -> tuple[np.ndarray, np.ndarray]:
    """Return a single ``(train_idx, val_idx)`` dual-OOD held-out partition.

    Perturbations and genes are independently hashed to ``[0, 1)``. Val rows have
    both a pert in the bottom ``pert_frac`` **and** a gene in the bottom
    ``gene_frac``; train rows have both a pert **and** a gene above their
    thresholds. Rows held out on exactly one axis are dropped (they would leak),
    so val is ~``pert_frac * gene_frac`` of the data and train ~the complement
    product. Mirrors the real test split's zero pert/gene overlap; stable given
    ``seed``.
    """
    pert_u = df[pert_col].map(lambda x: _unit(str(x), seed)).to_numpy()
    gene_u = df[gene_col].map(lambda x: _unit(str(x), seed)).to_numpy()
    idx = np.arange(len(df))
    val_mask = (pert_u < pert_frac) & (gene_u < gene_frac)
    train_mask = (pert_u >= pert_frac) & (gene_u >= gene_frac)
    return idx[train_mask], idx[val_mask]


def doubly_disjoint_folds(
    df: pd.DataFrame,
    k: int = 5,
    seed: int = 0,
    pert_col: str = "pert",
    gene_col: str = "gene",
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Yield ``k`` (train_idx, eval_idx) pairs with no shared pert or gene.

    Perturbations and genes are independently hashed into ``k`` buckets. For
    fold ``f``: eval rows have ``pert_bucket == f AND gene_bucket == f``; train
    rows have ``pert_bucket != f AND gene_bucket != f``. Rows where exactly one
    axis is held out are dropped from that fold (they would leak).
    """
    pert_bucket = df[pert_col].map(lambda x: _group(str(x), seed, k)).to_numpy()
    gene_bucket = df[gene_col].map(lambda x: _group(str(x), seed, k)).to_numpy()
    idx = np.arange(len(df))
    folds = []
    for f in range(k):
        eval_mask = (pert_bucket == f) & (gene_bucket == f)
        train_mask = (pert_bucket != f) & (gene_bucket != f)
        folds.append((idx[train_mask], idx[eval_mask]))
    return folds


def assert_leak_free(
    df: pd.DataFrame,
    train_idx: np.ndarray,
    eval_idx: np.ndarray,
    pert_col: str = "pert",
    gene_col: str = "gene",
) -> None:
    """Raise if any eval pert or gene also appears in train."""
    tr_perts = set(df.iloc[train_idx][pert_col])
    tr_genes = set(df.iloc[train_idx][gene_col])
    ev_perts = set(df.iloc[eval_idx][pert_col])
    ev_genes = set(df.iloc[eval_idx][gene_col])
    if tr_perts & ev_perts:
        raise AssertionError(f"pert leak: {sorted(tr_perts & ev_perts)[:5]}")
    if tr_genes & ev_genes:
        raise AssertionError(f"gene leak: {sorted(tr_genes & ev_genes)[:5]}")
