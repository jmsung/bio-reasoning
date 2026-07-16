"""Core Track A metric for internal (CV) evaluation.

Computes the same quantity as the official Kaggle scorer
(`kaggle_metric_track_a.py`): ``mean(AUROC_de, AUROC_dir)`` where DE ranks
none-vs-DE by ``up + down`` and DIR ranks up-vs-down by ``up / (up + down)`` on
DE-positive rows. This module drops the submission-schema/token checks so it can
score raw (labels, pred_up, pred_down) arrays during cross-validation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from bio_reasoning.eval.split import holdout_split

# Majority class is `none` (55.3% of train) — the accuracy a "predict none"
# classifier would get. Kept only as context: accuracy is NOT the metric.
MAJORITY_ACCURACY = 0.553


def evaluate(labels, pred_up, pred_down) -> dict[str, float]:
    """Return {auroc_de, auroc_dir, mean} for graded up/down predictions.

    The single scoring entry point every experiment and the trial-loop call.
    Computes the official Track A quantity (mean of AUROC_de and AUROC_dir)
    without the submission-schema checks, so it scores raw arrays directly.
    """
    labels = np.asarray(labels)
    pred_up = np.asarray(pred_up, dtype=float)
    pred_down = np.asarray(pred_down, dtype=float)

    de_true = (labels != "none").astype(int)
    de_score = pred_up + pred_down
    auroc_de = roc_auc_score(de_true, de_score) if len(set(de_true.tolist())) > 1 else float("nan")

    m = labels != "none"
    dir_true = (labels[m] == "up").astype(int)
    denom = pred_up[m] + pred_down[m]
    denom = np.where(denom == 0, 1.0, denom)
    dir_score = pred_up[m] / denom
    auroc_dir = (
        roc_auc_score(dir_true, dir_score) if len(set(dir_true.tolist())) > 1 else float("nan")
    )

    return {
        "auroc_de": float(auroc_de),
        "auroc_dir": float(auroc_dir),
        "mean": float((auroc_de + auroc_dir) / 2.0),
    }


# Back-compat alias: score_preds was the original name for the scorer.
score_preds = evaluate


def evaluate_on_split(
    df: pd.DataFrame,
    pred_up,
    pred_down,
    seed: int = 0,
    pert_frac: float = 0.4,
    gene_frac: float = 0.4,
) -> dict[str, float]:
    """Score full-length predictions on the dual-OOD held-out val partition.

    Applies :func:`holdout_split` and evaluates only the val rows — the fitness
    signal the trial-loop optimizes against. ``pred_up``/``pred_down`` are
    aligned to ``df`` rows. Returns the metric dict plus ``n_val``.
    """
    labels = df["label"].to_numpy()
    pred_up = np.asarray(pred_up, dtype=float)
    pred_down = np.asarray(pred_down, dtype=float)
    _, val = holdout_split(df, seed=seed, pert_frac=pert_frac, gene_frac=gene_frac)
    result = evaluate(labels[val], pred_up[val], pred_down[val])
    result["n_val"] = int(len(val))
    return result
