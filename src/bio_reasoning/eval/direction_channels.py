"""Build the three gate-passing DIRECTION channels' per-row ``r`` on an OOD split.

Extracted so every direction-axis experiment shares one channel-construction path
(DRY): the equal-weight ceiling probe (`scripts/dir_ceiling_probe.py`), the weighted
sweep + learned stacker (`scripts/weighted_direction_fuse.py`), and the TabPFN combiner
probe (`scripts/tabpfn_dir_eval.py`). Each channel supplies ``r`` = P(up|DE) per val
row; ``NaN`` marks rows it does not cover. ``dir_feature_matrix`` /
``oof_dir_feature_matrix`` stack the channels into a leak-free feature table for a
learned combiner (out-of-fold on the train partition, in-fold on the held-out rows).

- **GO-DIR** — two-stage GO model direction (`r = up/(up+down)`).
- **neighbour-DIR** — STRING-neighbour label borrowing (the incumbent, DIR-AUROC ~0.651).
- **embedding-DIR** — GenePert-style ridge over gene-text embeddings.

Data (train/GO/embedding/STRING caches, embeddings dict, STRING partners) is passed in
by the caller — this module does no I/O or network, so it stays import-cheap and testable.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

from bio_reasoning.eval.split import doubly_disjoint_folds, holdout_split
from bio_reasoning.features.gene_embeddings import fit_direction_ridge, gene_embedding_channel
from bio_reasoning.features.go_terms import GoPairFeaturizer
from bio_reasoning.features.neighbor_retrieval import neighbor_channel
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR

CHANNELS = ("GO-DIR", "neighbour-DIR", "embedding-DIR")


def go_dir_r(train_df: pd.DataFrame, val_df: pd.DataFrame, pert_cache, gene_cache) -> np.ndarray:
    """GO two-stage model direction on ``val_df``: ``r = up/(up+down)`` (fit on ``train_df``)."""
    model = TwoStageDEDIR(featurizer=GoPairFeaturizer(pert_cache, gene_cache)).fit(
        train_df["pert"], train_df["gene"], train_df["label"].to_numpy()
    )
    up, down = model.predict(val_df["pert"], val_df["gene"])
    denom = np.where(up + down == 0, 1.0, up + down)
    return up / denom


def neighbour_dir_r(
    train_df: pd.DataFrame, val_df: pd.DataFrame, partners: dict[str, set[str]]
) -> np.ndarray:
    """Neighbour-retrieval direction on ``val_df`` (train-only borrowing; ``NaN`` = uncovered)."""
    tp = set(train_df["pert"].astype(str))
    tg = set(train_df["gene"].astype(str))
    pnb = {p: partners.get(p, set()) & tp for p in val_df["pert"].astype(str).unique()}
    gnb = {g: partners.get(g, set()) & tg for g in val_df["gene"].astype(str).unique()}
    r = neighbor_channel(val_df[["pert", "gene"]].astype(str), train_df, pnb, gnb, min_support=3).r
    assert r is not None  # neighbor_channel always sets r
    return r


def embedding_dir_r(train_df: pd.DataFrame, val_df: pd.DataFrame, embeddings: dict) -> np.ndarray:
    """GenePert ridge direction on ``val_df`` (ridge fit on ``train_df`` DE rows; ``NaN`` = uncovered)."""
    ridge = fit_direction_ridge(train_df, embeddings)
    r = gene_embedding_channel(val_df[["pert", "gene"]], ridge, embeddings).r
    assert r is not None  # gene_embedding_channel always sets r
    return r


def seed_channels(
    df: pd.DataFrame,
    seed: int,
    *,
    embeddings: dict,
    partners: dict[str, set[str]],
    pert_cache,
    gene_cache,
) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    """Return ``(val_df, {channel: r})`` for one dual-OOD ``holdout_split`` seed (0.4/0.4)."""
    tr, va = holdout_split(df, seed=seed)
    train_df = df.iloc[tr].reset_index(drop=True)
    val_df = df.iloc[va].reset_index(drop=True)
    rs = {
        "GO-DIR": go_dir_r(train_df, val_df, pert_cache, gene_cache),
        "neighbour-DIR": neighbour_dir_r(train_df, val_df, partners),
        "embedding-DIR": embedding_dir_r(train_df, val_df, embeddings),
    }
    return val_df, rs


def dir_feature_matrix(
    train_df: pd.DataFrame,
    query_df: pd.DataFrame,
    *,
    partners: dict[str, set[str]],
    embeddings: dict,
    pert_cache,
    gene_cache,
) -> np.ndarray:
    """``(len(query_df), 3)`` matrix of per-channel ``P(up|DE)`` in ``CHANNELS`` order.

    Every channel is fit on ``train_df`` and predicted on ``query_df`` — leak-free as
    long as ``query_df`` shares no pert/gene with ``train_df``. ``NaN`` marks rows a
    channel does not cover (the combiner decides how to fill).
    """
    return np.column_stack(
        [
            go_dir_r(train_df, query_df, pert_cache, gene_cache),
            neighbour_dir_r(train_df, query_df, partners),
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
    ``(len(query_df), n_feat)`` array for its eval rows. Each row is predicted only by a
    fold that excludes its pert **and** gene, so the features match the dual-OOD regime
    of the outer held-out set — the correct training signal for a combiner. Returns
    ``(X, covered)``: ``X`` is ``NaN`` on rows no fold evaluated (``doubly_disjoint_folds``
    drops singly-held rows); ``covered`` marks the rest.
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
    pert_cache,
    gene_cache,
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
        )

    return cross_fitted_features(train_df, build, k=k, seed=seed)
