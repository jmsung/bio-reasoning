"""Evaluate the learned two-stage DE×DIR model on the dual-OOD split.

Tests the branch hypothesis: do learned P(DE) and P(up|DE) heads over stateless
pair-string features (`features/pair_features.py`) beat the hand-set evidence
prior on the leak-free split where every pert and gene is unseen? Reports
``mean(AUROC_de, AUROC_dir)`` on the holdout val partition and under 5-fold
doubly-disjoint CV, against the prior floor (~0.533) and the no-signal 0.5.

Run: uv run --group eval python scripts/two_stage_de_dir_eval.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from bio_reasoning.eval.split import assert_leak_free, doubly_disjoint_folds, holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.features.gene_function import annotate_perts
from bio_reasoning.models import track_a_prior
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
CACHE = ROOT / "data/interim/pert_go_category.json"
K = 5
SEED = 0
PRIOR_FLOOR = 0.533


def _two_stage_holdout(df: pd.DataFrame, labels: np.ndarray) -> dict[str, float]:
    tr, val = holdout_split(df, seed=SEED)
    assert_leak_free(df, tr, val)
    model = TwoStageDEDIR().fit(df.pert.iloc[tr], df.gene.iloc[tr], labels[tr])
    up, down = model.predict(df.pert.iloc[val], df.gene.iloc[val])
    r = evaluate(labels[val], up, down)
    r["n_val"] = int(len(val))
    return r


def _two_stage_cv(df: pd.DataFrame, labels: np.ndarray) -> tuple[float, float]:
    means = []
    for tr, ev in doubly_disjoint_folds(df, k=K, seed=SEED):
        assert_leak_free(df, tr, ev)
        model = TwoStageDEDIR().fit(df.pert.iloc[tr], df.gene.iloc[tr], labels[tr])
        up, down = model.predict(df.pert.iloc[ev], df.gene.iloc[ev])
        means.append(evaluate(labels[ev], up, down)["mean"])
    return float(np.nanmean(means)), float(np.nanstd(means))


def main() -> None:
    df = pd.read_csv(TRAIN)
    labels = df.label.to_numpy()
    print(f"train: {len(df)} rows, {df.pert.nunique()} perts, {df.gene.nunique()} genes")

    cats = annotate_perts(df.pert.tolist(), CACHE)
    up_prior, dn_prior = track_a_prior.predict(df.pert.tolist(), cats)
    const = np.full(len(df), 0.5)

    tr, val = holdout_split(df, seed=SEED)
    print("\n== dual-OOD holdout val ==")
    print(f"{'model':<22}{'auroc_de':>10}{'auroc_dir':>11}{'mean':>8}")
    for name, up, down in [
        ("no-signal (0.5/0.5)", const[val], const[val]),
        ("evidence prior", up_prior[val], dn_prior[val]),
    ]:
        r = evaluate(labels[val], up, down)
        print(f"{name:<22}{r['auroc_de']:>10.3f}{r['auroc_dir']:>11.3f}{r['mean']:>8.3f}")
    ts = _two_stage_holdout(df, labels)
    print(
        f"{'two-stage (learned)':<22}{ts['auroc_de']:>10.3f}{ts['auroc_dir']:>11.3f}{ts['mean']:>8.3f}"
    )

    print("\n== 5-fold doubly-disjoint CV (mean ± std) ==")
    prior_cv = [
        evaluate(labels[ev], up_prior[ev], dn_prior[ev])["mean"]
        for _, ev in doubly_disjoint_folds(df, k=K, seed=SEED)
    ]
    print(f"{'evidence prior':<22}{np.nanmean(prior_cv):>8.3f} ± {np.nanstd(prior_cv):.3f}")
    mu, sd = _two_stage_cv(df, labels)
    print(f"{'two-stage (learned)':<22}{mu:>8.3f} ± {sd:.3f}")

    verdict = "beats" if mu > PRIOR_FLOOR else "does NOT beat"
    print(
        f"\nVerdict: the learned two-stage model {verdict} the prior floor "
        f"({mu:.3f} vs {PRIOR_FLOOR}). Gene/pert symbols are largely arbitrary "
        "strings; the prior's signal is GO biology, which char-ngrams only weakly proxy."
    )


if __name__ == "__main__":
    main()
