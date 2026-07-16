"""Honest baseline table on the dual-OOD validation split + the CV-inflation story.

Re-scores the known Track A baselines on the leak-free held-out split
(:func:`holdout_split`) so every number is comparable to the real test split
(perturbations *and* genes disjoint from train). Also demonstrates *why* a naive
CV inflates — the mechanism behind Track B's reported CV 0.675 vs its realized
public-LB 0.488: a fold-fitted per-pert memorizing baseline scores high under
random-row CV (same perts in train and eval) and collapses to chance under
dual-OOD CV (every eval pert unseen). A fixed functional prior, by contrast,
cannot leak, so it is CV-stable.

Run: uv run --group eval python scripts/ood_val_baselines.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from bio_reasoning.eval.split import assert_leak_free, doubly_disjoint_folds, holdout_split
from bio_reasoning.eval.track_a_score import evaluate, evaluate_on_split
from bio_reasoning.features.gene_function import annotate_perts
from bio_reasoning.models import track_a_prior

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
CACHE = ROOT / "data/interim/pert_go_category.json"
K = 5
SEED = 0

# Track B's own numbers (see mb finding project_track_b_lb_0488): a 60-row CV
# read 0.675, the realized public LB was 0.488 — a 0.187 inflation gap.
TRACK_B_CV = 0.675
TRACK_B_LB = 0.488


def _random_folds(n: int, k: int, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """Naive random-row k-fold — perts/genes overlap between train and eval."""
    idx = np.random.default_rng(seed).permutation(n)
    return [(np.setdiff1d(idx, chunk), chunk) for chunk in np.array_split(idx, k)]


def _memorizing_predict(
    df: pd.DataFrame, train_idx: np.ndarray, eval_idx: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Per-pert label-frequency predictor fitted on the train fold.

    Predicts each eval row from its perturbation's up/down frequency in the
    train fold; an unseen pert falls back to 0.5/0.5 (chance). This is the
    baseline that memorizes pert identity — high under naive CV, chance OOD.
    """
    tr = df.iloc[train_idx]
    up_freq = tr.assign(v=(tr.label == "up").astype(float)).groupby("pert").v.mean()
    dn_freq = tr.assign(v=(tr.label == "down").astype(float)).groupby("pert").v.mean()
    ev_pert = df.iloc[eval_idx].pert
    up = ev_pert.map(up_freq).fillna(0.5).to_numpy()
    down = ev_pert.map(dn_freq).fillna(0.5).to_numpy()
    return up, down


def _cv_mean(df: pd.DataFrame, folds, up: np.ndarray, down: np.ndarray) -> float:
    """Mean fold score for *fixed* full-length predictions over given folds."""
    labels = df.label.to_numpy()
    means = [evaluate(labels[ev], up[ev], down[ev])["mean"] for _, ev in folds]
    return float(np.nanmean(means))


def _memorizing_cv_mean(df: pd.DataFrame, folds) -> float:
    """Mean fold score for the *fold-fitted* memorizing baseline."""
    labels = df.label.to_numpy()
    means = []
    for tr, ev in folds:
        up, down = _memorizing_predict(df, tr, ev)
        means.append(evaluate(labels[ev], up, down)["mean"])
    return float(np.nanmean(means))


def main() -> None:
    df = pd.read_csv(TRAIN)
    tr_idx, val_idx = holdout_split(df, seed=SEED)
    assert_leak_free(df, tr_idx, val_idx)
    print(
        f"train: {len(df)} rows, {df.pert.nunique()} perts, {df.gene.nunique()} genes | "
        f"dual-OOD holdout val: {len(val_idx)} rows (train portion {len(tr_idx)})"
    )

    cats = annotate_perts(df.pert.tolist(), CACHE)
    up_prior, dn_prior = track_a_prior.predict(df.pert.tolist(), cats)
    const = np.full(len(df), 0.5)

    print("\n== honest baseline table on the dual-OOD held-out val split ==")
    print(f"{'baseline':<24}{'auroc_de':>10}{'auroc_dir':>11}{'mean':>8}")
    for name, up, down in [
        ("no-signal (0.5/0.5)", const, const),
        ("evidence prior", up_prior, dn_prior),
    ]:
        r = evaluate_on_split(df, up, down, seed=SEED)
        print(f"{name:<24}{r['auroc_de']:>10.3f}{r['auroc_dir']:>11.3f}{r['mean']:>8.3f}")

    ood_folds = doubly_disjoint_folds(df, k=K, seed=SEED)
    rnd_folds = _random_folds(len(df), K, SEED)

    print(f"\n== why a naive CV inflates (k={K}) ==")
    print(f"{'baseline':<24}{'naive random CV':>18}{'dual-OOD CV':>14}{'gap':>8}")
    prior_naive = _cv_mean(df, rnd_folds, up_prior, dn_prior)
    prior_ood = _cv_mean(df, ood_folds, up_prior, dn_prior)
    print(
        f"{'evidence prior':<24}{prior_naive:>18.3f}{prior_ood:>14.3f}"
        f"{prior_naive - prior_ood:>8.3f}  (fixed fn — can't leak)"
    )
    mem_naive = _memorizing_cv_mean(df, rnd_folds)
    mem_ood = _memorizing_cv_mean(df, ood_folds)
    print(
        f"{'memorizing (per-pert)':<24}{mem_naive:>18.3f}{mem_ood:>14.3f}"
        f"{mem_naive - mem_ood:>8.3f}  (leaks pert identity)"
    )

    print(
        f"\nTrack B (reported): CV {TRACK_B_CV:.3f} vs realized public LB {TRACK_B_LB:.3f} "
        f"= {TRACK_B_CV - TRACK_B_LB:.3f} inflation gap — the same collapse the memorizing\n"
        "baseline shows. Trust the dual-OOD split, not a naive/small CV."
    )


if __name__ == "__main__":
    main()
