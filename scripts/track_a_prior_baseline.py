"""Evaluate the Track A evidence-grounded prior on a leak-free split.

Establishes the floor that agentic Track B must beat. Reports
``mean(AUROC_de, AUROC_dir)`` (the official metric) under doubly-disjoint CV,
against a no-signal constant baseline.

Run: uv run --group eval python scripts/track_a_prior_baseline.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from bio_reasoning.eval.split import assert_leak_free, doubly_disjoint_folds
from bio_reasoning.eval.track_a_score import MAJORITY_ACCURACY, score_preds
from bio_reasoning.features.gene_function import annotate_perts
from bio_reasoning.models import track_a_prior

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
CACHE = ROOT / "data/interim/pert_go_category.json"
K = 5
SEED = 0


def _fmt(d: dict[str, float]) -> str:
    return f"de={d['auroc_de']:.3f}  dir={d['auroc_dir']:.3f}  mean={d['mean']:.3f}"


def main() -> None:
    df = pd.read_csv(TRAIN)
    print(f"train: {len(df)} rows, {df.pert.nunique()} perts, {df.gene.nunique()} genes")

    cats = annotate_perts(df.pert.tolist(), CACHE)
    counts = pd.Series(list(cats.values())).value_counts().to_dict()
    print(f"pert categories: {counts}")

    up, down = track_a_prior.predict(df.pert.tolist(), cats)
    labels = df.label.to_numpy()

    # No-signal reference: constant 0.5/0.5 → mean AUROC 0.5.
    const = np.full(len(df), 0.5)

    print(f"\n{'baseline':<22}{'pooled (all rows)':<34}{'leak-free CV (mean±std)'}")
    for name, pu, pdn in [("constant (no signal)", const, const), ("prior (functional)", up, down)]:
        pooled = score_preds(labels, pu, pdn)
        fold_means = []
        for tr, ev in doubly_disjoint_folds(df, k=K, seed=SEED):
            assert_leak_free(df, tr, ev)
            fold_means.append(score_preds(labels[ev], pu[ev], pdn[ev])["mean"])
        fm = np.array(fold_means, dtype=float)
        cv = f"{np.nanmean(fm):.3f} ± {np.nanstd(fm):.3f}  (n_eval≈{int(np.mean([len(ev) for _, ev in doubly_disjoint_folds(df, k=K, seed=SEED)]))})"
        print(f"{name:<22}{_fmt(pooled):<34}{cv}")

    print(
        f"\n(context: majority-class accuracy = {MAJORITY_ACCURACY}; but the metric is AUROC, not accuracy)"
    )


if __name__ == "__main__":
    main()
