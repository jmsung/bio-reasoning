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
    group_rate_loo,
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
