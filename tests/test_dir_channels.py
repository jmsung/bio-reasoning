"""Leak-free DIRECTION channel feature assembly for the TabPFN combiner.

Covers the pure plumbing that needs no external caches: the neighbour-DIR
r-builder (STRING partners restricted to the train universe) and the generic
out-of-fold cross-fitter that produces leak-free training features over the
dual-OOD inner folds.
"""

import numpy as np
import pandas as pd

from bio_reasoning.features.dir_channels import (
    cross_fitted_features,
    neighbour_dir_r,
)


def _df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "pert": ["Pa", "Pa", "Pb", "Pc", "Pc", "Pd"],
            "gene": ["G1", "G2", "G1", "G3", "G4", "G4"],
            "label": ["up", "none", "up", "down", "none", "down"],
        }
    )


def test_neighbour_dir_r_borrows_train_direction_leak_free():
    train = _df()
    query = pd.DataFrame({"pert": ["Pq"], "gene": ["G1"]})
    # Pq's partner Pa is in train; G1's neighbours restricted to train universe.
    partners = {"Pq": {"Pa"}, "G1": {"G2"}}
    r = neighbour_dir_r(train, query, partners, min_support=1)
    assert r.shape == (1,)
    # Retrieved train rows: pert==Pa (up, none) or gene==G2 (none). DE rows = {up}.
    assert r[0] == 1.0


def test_neighbour_dir_r_uncovered_is_nan():
    train = _df()
    query = pd.DataFrame({"pert": ["Zz"], "gene": ["Yy"]})
    r = neighbour_dir_r(train, query, partners={}, min_support=1)
    assert np.isnan(r[0])


def test_cross_fitted_features_placement_and_coverage():
    # 4 perts x 4 genes fully crossed → doubly-disjoint folds cover a subset of rows.
    rows = [(f"P{p}", f"G{g}") for p in range(4) for g in range(4)]
    df = pd.DataFrame(rows, columns=["pert", "gene"])
    df["val"] = np.arange(len(df), dtype=float)

    # build_fn just echoes each query row's own `val` — lets us assert correct
    # per-fold row alignment without touching any real channel/cache.
    def build_fn(train_df, query_df):
        return query_df[["val"]].to_numpy(dtype=float)

    X, covered = cross_fitted_features(df, build_fn, k=4, seed=0)
    assert X.shape == (len(df), 1)
    # Covered rows carry their own value; uncovered rows stay NaN.
    assert np.allclose(X[covered, 0], df["val"].to_numpy()[covered])
    assert np.isnan(X[~covered, 0]).all()
    assert covered.any()


def test_cross_fitted_features_train_rows_never_leak_into_own_fold():
    rows = [(f"P{p}", f"G{g}") for p in range(4) for g in range(4)]
    df = pd.DataFrame(rows, columns=["pert", "gene"])

    seen = {"leak": False}

    def build_fn(train_df, query_df):
        tr_perts = set(train_df["pert"])
        tr_genes = set(train_df["gene"])
        for p, g in zip(query_df["pert"], query_df["gene"], strict=True):
            if p in tr_perts or g in tr_genes:
                seen["leak"] = True
        return np.zeros((len(query_df), 1))

    cross_fitted_features(df, build_fn, k=4, seed=0)
    assert not seen["leak"]
