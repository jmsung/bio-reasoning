"""Build the three gate-passing DIRECTION channels' per-row ``r`` on an OOD split.

Extracted so every direction-axis experiment shares one channel-construction path
(DRY): the equal-weight ceiling probe (`scripts/dir_ceiling_probe.py`), the weighted
sweep + learned stacker (`scripts/weighted_direction_fuse.py`). Each channel supplies
``r`` = P(up|DE) per val row; ``NaN`` marks rows it does not cover.

- **GO-DIR** — two-stage GO model direction (`r = up/(up+down)`).
- **neighbour-DIR** — STRING-neighbour label borrowing (the incumbent, DIR-AUROC ~0.651).
- **embedding-DIR** — GenePert-style ridge over gene-text embeddings.

Data (train/GO/embedding/STRING caches, embeddings dict, STRING partners) is passed in
by the caller — this module does no I/O or network, so it stays import-cheap and testable.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bio_reasoning.eval.split import holdout_split
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
