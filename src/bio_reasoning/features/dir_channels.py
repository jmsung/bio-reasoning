"""Leak-free per-pair DIRECTION features for a learned combiner.

Each channel r-builder fits its DIRECTION model on a train partition and returns
``P(up | DE)`` for query rows (``NaN`` where the channel does not cover a row).
Factored out of ``scripts/dir_ceiling_probe.py`` so the ceiling probe and the
TabPFN combiner share one implementation (no duplicated recipes).

``cross_fitted_features`` produces the leak-free *training* feature matrix: a
combiner that stacks these channels must be trained on out-of-fold predictions,
generated over the same dual-OOD regime as the held-out rows it will score.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

from bio_reasoning.eval.split import doubly_disjoint_folds
from bio_reasoning.features.gene_embeddings import fit_direction_ridge, gene_embedding_channel
from bio_reasoning.features.go_terms import GoPairFeaturizer
from bio_reasoning.features.neighbor_retrieval import neighbor_channel
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR

CHANNELS = ("GO-DIR", "neighbour-DIR", "embedding-DIR")


def go_dir_r(
    train_df: pd.DataFrame, query_df: pd.DataFrame, pert_cache: str, gene_cache: str
) -> np.ndarray:
    """GO two-stage direction ``P(up|DE)`` for ``query_df``, fit on ``train_df``."""
    model = TwoStageDEDIR(featurizer=GoPairFeaturizer(pert_cache, gene_cache)).fit(
        train_df["pert"], train_df["gene"], train_df["label"].to_numpy()
    )
    up, down = model.predict(query_df["pert"], query_df["gene"])
    denom = np.where(up + down == 0, 1.0, up + down)
    return up / denom


def neighbour_dir_r(
    train_df: pd.DataFrame,
    query_df: pd.DataFrame,
    partners: dict[str, set[str]],
    min_support: int = 3,
) -> np.ndarray:
    """STRING-neighbour borrowed direction; ``NaN`` below ``min_support`` support."""
    tp = set(train_df["pert"].astype(str))
    tg = set(train_df["gene"].astype(str))
    pnb = {p: partners.get(p, set()) & tp for p in query_df["pert"].astype(str).unique()}
    gnb = {g: partners.get(g, set()) & tg for g in query_df["gene"].astype(str).unique()}
    r = neighbor_channel(
        query_df[["pert", "gene"]].astype(str), train_df, pnb, gnb, min_support=min_support
    ).r
    assert r is not None  # neighbor_channel always sets the direction bus
    return r


def embedding_dir_r(train_df: pd.DataFrame, query_df: pd.DataFrame, embeddings: dict) -> np.ndarray:
    """GenePert-style embedding ridge direction; ``NaN`` where a symbol lacks a vector."""
    ridge = fit_direction_ridge(train_df, embeddings)
    r = gene_embedding_channel(query_df[["pert", "gene"]], ridge, embeddings).r
    assert r is not None
    return r


def dir_feature_matrix(
    train_df: pd.DataFrame,
    query_df: pd.DataFrame,
    *,
    partners: dict[str, set[str]],
    embeddings: dict,
    pert_cache: str,
    gene_cache: str,
    min_support: int = 3,
) -> np.ndarray:
    """``(len(query_df), 3)`` matrix of per-channel ``P(up|DE)`` in ``CHANNELS`` order.

    Every channel is fit on ``train_df`` and predicted on ``query_df`` — leak-free
    as long as ``query_df`` shares no pert/gene with ``train_df``. Columns carry
    ``NaN`` where a channel does not cover a row (the combiner decides how to fill).
    """
    return np.column_stack(
        [
            go_dir_r(train_df, query_df, pert_cache, gene_cache),
            neighbour_dir_r(train_df, query_df, partners, min_support=min_support),
            embedding_dir_r(train_df, query_df, embeddings),
        ]
    )


def cross_fitted_features(
    df: pd.DataFrame,
    build_fn: Callable[[pd.DataFrame, pd.DataFrame], np.ndarray],
    *,
    k: int = 5,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """Out-of-fold features over ``df`` via dual-OOD inner folds.

    ``build_fn(train_df, query_df)`` fits on a fold's train rows and returns a
    ``(len(query_df), n_feat)`` array for its eval rows. Each row is predicted only
    by a fold that excludes its pert **and** gene, so the returned features match
    the dual-OOD regime of the outer held-out set — the correct training signal for
    a combiner. Returns ``(X, covered)``: ``X`` is ``NaN`` on rows no fold evaluated
    (``doubly_disjoint_folds`` drops singly-held rows); ``covered`` marks the rest.
    """
    n = len(df)
    X: np.ndarray | None = None
    covered = np.zeros(n, dtype=bool)
    for tr, ev in doubly_disjoint_folds(df, k=k, seed=seed):
        if len(ev) == 0 or len(tr) == 0:
            continue
        feats = np.asarray(
            build_fn(df.iloc[tr].reset_index(drop=True), df.iloc[ev].reset_index(drop=True)),
            dtype=float,
        )
        if X is None:
            X = np.full((n, feats.shape[1]), np.nan)
        X[ev] = feats
        covered[ev] = True
    if X is None:
        X = np.full((n, 0), np.nan)
    return X, covered


def oof_dir_feature_matrix(
    train_df: pd.DataFrame,
    *,
    partners: dict[str, set[str]],
    embeddings: dict,
    pert_cache: str,
    gene_cache: str,
    min_support: int = 3,
    k: int = 5,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """Cross-fitted ``dir_feature_matrix`` over ``train_df`` — leak-free combiner input."""

    def build(tr: pd.DataFrame, ev: pd.DataFrame) -> np.ndarray:
        return dir_feature_matrix(
            tr,
            ev,
            partners=partners,
            embeddings=embeddings,
            pert_cache=pert_cache,
            gene_cache=gene_cache,
            min_support=min_support,
        )

    return cross_fitted_features(train_df, build, k=k, seed=seed)
