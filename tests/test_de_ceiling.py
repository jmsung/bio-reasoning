"""Offline tests for the DE-learnability ceiling oracle (leakage-allowed features).

The oracle deliberately crosses the leak-free split boundary to UPPER-BOUND AUROC_de:
if even a head that knows each gene/pert's true DE propensity can't separate DE from
none on held-out pairs, DE is unlearnable by design. These tests pin the leave-one-out
marginal encoding (self excluded → not per-pair label leakage) and its provenance.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bio_reasoning.eval.de_ceiling import (
    ORACLE_FEATURES,
    de_auroc,
    de_ceiling_probe,
    group_rate_loo,
    marginal_rate,
    oracle_de_features,
)


def test_group_rate_loo_excludes_self() -> None:
    """LOO rate for a row = DE-rate over the group's OTHER rows (self removed)."""
    keys = np.array(["g", "g", "g"])
    de = np.array([1, 0, 1])
    prior = 0.5
    out = group_rate_loo(keys, de, prior)
    # row0: others [0,1] → 0.5 ; row1: others [1,1] → 1.0 ; row2: others [1,0] → 0.5
    assert np.allclose(out, [0.5, 1.0, 0.5])


def test_group_rate_loo_singleton_falls_back_to_prior() -> None:
    """A group of size 1 has no 'other' rows → the global prior, never its own label."""
    keys = np.array(["a", "b", "b"])
    de = np.array([1, 0, 1])
    prior = 0.3
    out = group_rate_loo(keys, de, prior)
    assert out[0] == 0.3  # singleton 'a' → prior, NOT its label 1
    assert np.allclose(out[1:], [1.0, 0.0])  # 'b' pair, LOO


def test_oracle_features_shape_and_names() -> None:
    """oracle_de_features returns one column per named oracle feature."""
    df = pd.DataFrame(
        {
            "pert": ["p0", "p0", "p1", "p1"],
            "gene": ["g0", "g1", "g0", "g1"],
            "label": ["up", "none", "down", "none"],
        }
    )
    X = oracle_de_features(df)
    assert X.shape == (4, len(ORACLE_FEATURES))
    assert ORACLE_FEATURES == ("gene_de_rate", "pert_de_rate", "gene_count", "pert_count")


def test_oracle_gene_rate_is_leave_one_out() -> None:
    """The gene_de_rate column excludes the row's own label (marginal, not per-pair)."""
    df = pd.DataFrame(
        {
            "pert": ["p0", "p1", "p2"],
            "gene": ["g0", "g0", "g0"],  # one gene, three pairs
            "label": ["up", "none", "up"],  # de = [1, 0, 1]
        }
    )
    X = oracle_de_features(df)
    gene_rate = X[:, ORACLE_FEATURES.index("gene_de_rate")]
    # LOO over de=[1,0,1]: row0 others[0,1]=0.5, row1 others[1,1]=1.0, row2 others[1,0]=0.5
    assert np.allclose(gene_rate, [0.5, 1.0, 0.5])
    # gene_count is the full multiplicity (a marginal stat, self included)
    assert np.allclose(X[:, ORACLE_FEATURES.index("gene_count")], [3, 3, 3])


def test_marginal_rate_unseen_key_is_prior() -> None:
    """A key absent from train scores the prior — never a val label (honest transfer)."""
    all_keys = ["a", "b", "c"]  # 'c' is unseen in train
    train_keys = ["a", "a", "b"]
    train_de = [1, 1, 0]
    out = marginal_rate(all_keys, train_keys, train_de, prior=0.4)
    assert np.allclose(out, [1.0, 0.0, 0.4])  # a→1.0, b→0.0, c(unseen)→prior


def test_de_auroc_single_class_is_nan() -> None:
    """A val fold with only one DE class can't be scored → nan, never a fake number."""
    assert np.isnan(de_auroc(np.array([1, 1, 1]), np.array([0.2, 0.8, 0.5])))
    assert de_auroc(np.array([1, 0]), np.array([0.9, 0.1])) == 1.0


def _structured_frame(n_genes: int = 40, rows_per_gene: int = 12) -> pd.DataFrame:
    """Each gene is deterministically all-DE or all-none; perts cycle (no pert signal)."""
    rows = []
    for gi in range(n_genes):
        de_gene = gi % 2 == 0  # half the genes are always-DE, half always-none
        for r in range(rows_per_gene):
            rows.append(
                {
                    "pert": f"p{r % 20}",
                    "gene": f"g{gi}",
                    "label": "up" if de_gene else "none",
                }
            )
    return pd.DataFrame(rows)


def test_leaked_ceiling_is_a_mirage_honest_transfer_is_not() -> None:
    """Perfectly gene-determined DE: the LEAKED head recovers it, the HONEST head can't.

    The structure is real, but on a dual-OOD split every val gene is unseen in train,
    so the honest train-derived rate collapses to the prior (≈chance) — that is exactly
    why the leaked 0.9x number is a mirage, not usable signal. This pins the core
    finding of the probe.
    """
    df = _structured_frame()
    out = de_ceiling_probe(df, seeds=(0, 1, 2))
    assert out["leaked_head"][0] > 0.9  # intra-val leakage recovers the structure
    assert out["gene_de_rate"][0] < 0.65  # honest transfer: held-out genes → prior, ≈chance
    assert out["fitted_head"][0] < 0.75  # honest bound far below the leaked mirage


def test_probe_returns_all_channels() -> None:
    """The probe reports (mean, std) for every oracle feature + honest & leaked heads."""
    df = _structured_frame()
    out = de_ceiling_probe(df, seeds=(0, 1))
    for key in (*ORACLE_FEATURES, "fitted_head", "leaked_head"):
        assert key in out and len(out[key]) == 2
