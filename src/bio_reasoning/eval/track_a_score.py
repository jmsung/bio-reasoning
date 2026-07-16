"""Core Track A metric for internal (CV) evaluation.

Computes the same quantity as the official Kaggle scorer
(`kaggle_metric_track_a.py`): ``mean(AUROC_de, AUROC_dir)`` where DE ranks
none-vs-DE by ``up + down`` and DIR ranks up-vs-down by ``up / (up + down)`` on
DE-positive rows. This module drops the submission-schema/token checks so it can
score raw (labels, pred_up, pred_down) arrays during cross-validation.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score

# Majority class is `none` (55.3% of train) — the accuracy a "predict none"
# classifier would get. Kept only as context: accuracy is NOT the metric.
MAJORITY_ACCURACY = 0.553


def score_preds(labels, pred_up, pred_down) -> dict[str, float]:
    """Return {auroc_de, auroc_dir, mean} for graded up/down predictions."""
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
