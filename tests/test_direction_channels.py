"""Leak-free DIRECTION feature assembly for the TabPFN combiner.

Covers the pure plumbing in ``bio_reasoning.eval.direction_channels`` that needs no
external caches: the neighbour-DIR r-builder (STRING partners restricted to the train
universe) and the generic out-of-fold cross-fitter that produces the leak-free training
features for a stacked combiner.
"""

import numpy as np
import pandas as pd

from bio_reasoning.eval.direction_channels import (
    cross_fitted_features,
    neighbour_dir_r,
)


def test_neighbour_dir_r_borrows_train_direction_leak_free():
    # Pq's partner Pa appears in 3 train rows (meets the fixed min_support=3), all "up".
    train = pd.DataFrame(
        {
            "pert": ["Pa", "Pa", "Pa", "Pb", "Pc"],
            "gene": ["G1", "G2", "G3", "G4", "G5"],
            "label": ["up", "up", "up", "none", "down"],
        }
    )
    query = pd.DataFrame({"pert": ["Pq"], "gene": ["Gq"]})
    partners = {"Pq": {"Pa"}}
    r = neighbour_dir_r(train, query, partners)
    assert r.shape == (1,)
    assert r[0] == 1.0  # 3 retrieved DE rows, all up


def test_neighbour_dir_r_uncovered_is_nan():
    train = pd.DataFrame(
        {
            "pert": ["Pa", "Pb", "Pc"],
            "gene": ["G1", "G2", "G3"],
            "label": ["up", "down", "none"],
        }
    )
    query = pd.DataFrame({"pert": ["Zz"], "gene": ["Yy"]})
    r = neighbour_dir_r(train, query, partners={})
    assert np.isnan(r[0])


def test_cross_fitted_features_placement_and_coverage():
    # 4 perts x 4 genes fully crossed → doubly-disjoint folds cover a subset of rows.
    rows = [(f"P{p}", f"G{g}") for p in range(4) for g in range(4)]
    df = pd.DataFrame(rows, columns=["pert", "gene"])
    df["val"] = np.arange(len(df), dtype=float)

    # build_fn echoes each query row's own `val` — asserts correct per-fold row
    # alignment without touching any real channel/cache.
    def build_fn(train_df, query_df):
        return query_df[["val"]].to_numpy(dtype=float)

    X, covered = cross_fitted_features(df, build_fn, k=4, seed=0)
    assert X.shape == (len(df), 1)
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
