"""Error-structure decomposition for the Track A incumbent pipeline.

The trial loop has told us *whether* each change moved the mean AUROC, never
*where* the best pipeline is wrong. This module dissects the incumbent
(two-stage GO DE + neighbour-fused direction, LB 0.585) on the dual-OOD holdout
along the two axes the metric actually sums:

- **DE axis** — none-vs-DE ranked by ``up + down`` (the known-hard half).
- **DIR axis** — up-vs-down ranked by ``up / (up + down)`` on DE rows.

Everything here is pure given ``(labels, up, down, covered, category)`` arrays so
it is unit-testable; the pipeline that produces those arrays lives in
``scripts/track_a_error_structure.py`` (I/O + model fit).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def _safe_auroc(y_true: np.ndarray, score: np.ndarray) -> float:
    """ROC-AUC, or ``nan`` when a group is single-class / empty (can't rank)."""
    y_true = np.asarray(y_true)
    if y_true.size == 0 or len(np.unique(y_true)) < 2:
        return float("nan")
    return float(roc_auc_score(y_true, np.asarray(score, dtype=float)))


def axis_scores(labels: np.ndarray, up: np.ndarray, down: np.ndarray) -> dict[str, float]:
    """Return ``{auroc_de, auroc_dir, mean, n, n_de}`` for one row group.

    Mirrors ``eval.track_a_score.evaluate`` but tolerates single-class groups
    (returns ``nan`` for that axis) so it can be applied per category.
    """
    labels = np.asarray(labels)
    up = np.asarray(up, dtype=float)
    down = np.asarray(down, dtype=float)

    de_true = (labels != "none").astype(int)
    auroc_de = _safe_auroc(de_true, up + down)

    m = labels != "none"
    denom = np.where((up[m] + down[m]) == 0, 1.0, up[m] + down[m])
    auroc_dir = _safe_auroc((labels[m] == "up").astype(int), up[m] / denom)

    return {
        "auroc_de": auroc_de,
        "auroc_dir": auroc_dir,
        "mean": (auroc_de + auroc_dir) / 2.0,
        "n": int(labels.size),
        "n_de": int(m.sum()),
    }


def axis_gap_budget(labels: np.ndarray, up: np.ndarray, down: np.ndarray) -> dict[str, float]:
    """How much headroom each axis holds — ``1 - AUROC`` per axis and its share.

    The mean metric weights the two axes equally, so the *marginal* value of a
    lever is proportional to that axis's remaining gap. ``de_share`` is the
    fraction of total remaining gap that lives on the DE axis.
    """
    s = axis_scores(labels, up, down)
    de_gap = 1.0 - s["auroc_de"]
    dir_gap = 1.0 - s["auroc_dir"]
    total = de_gap + dir_gap
    return {
        "auroc_de": s["auroc_de"],
        "auroc_dir": s["auroc_dir"],
        "de_gap": de_gap,
        "dir_gap": dir_gap,
        "de_share": de_gap / total if total > 0 else float("nan"),
    }


def per_group_axis(
    labels: np.ndarray,
    up: np.ndarray,
    down: np.ndarray,
    group: np.ndarray,
    min_n: int = 30,
) -> pd.DataFrame:
    """Per-group DE-rate and per-axis AUROC. Groups with ``< min_n`` rows dropped."""
    df = pd.DataFrame(
        {"label": np.asarray(labels), "up": up, "down": down, "group": np.asarray(group)}
    )
    rows = []
    for g, sub in df.groupby("group"):
        if len(sub) < min_n:
            continue
        s = axis_scores(sub["label"].to_numpy(), sub["up"].to_numpy(), sub["down"].to_numpy())
        de_rate = float((sub["label"].to_numpy() != "none").mean())
        up_frac = float((sub["label"].to_numpy() == "up")[sub["label"].to_numpy() != "none"].mean())
        rows.append(
            {
                "group": g,
                "n": s["n"],
                "n_de": s["n_de"],
                "de_rate": de_rate,
                "up_frac_of_de": up_frac,
                "auroc_de": s["auroc_de"],
                "auroc_dir": s["auroc_dir"],
            }
        )
    return pd.DataFrame(rows).sort_values("n", ascending=False).reset_index(drop=True)


def coverage_dir_effect(
    labels: np.ndarray, up: np.ndarray, down: np.ndarray, covered: np.ndarray
) -> pd.DataFrame:
    """DIR-AUROC split by whether the neighbour channel covered the row.

    Quantifies the coverage lever: if covered rows have a much higher DIR-AUROC
    than uncovered (base-only) rows, extending neighbour coverage is a direct win.
    """
    labels = np.asarray(labels)
    covered = np.asarray(covered, dtype=bool)
    rows = []
    for name, mask in (("covered", covered), ("uncovered", ~covered)):
        s = axis_scores(labels[mask], np.asarray(up)[mask], np.asarray(down)[mask])
        rows.append({"subset": name, "n": s["n"], "n_de": s["n_de"], "auroc_dir": s["auroc_dir"]})
    return pd.DataFrame(rows)


def confident_wrong(
    labels: np.ndarray,
    up: np.ndarray,
    down: np.ndarray,
    dir_hi: float = 0.75,
    dir_lo: float = 0.25,
) -> pd.DataFrame:
    """Per-row table of *confident direction* DE rows, flagged right/wrong.

    A row is confident when ``dir_score = up/(up+down)`` is outside
    ``[dir_lo, dir_hi]``; it is wrong when the confident call disagrees with the
    true up/down label. Returned frame lets the caller cross-tab wrongness
    against category (the lever hunt).
    """
    labels = np.asarray(labels)
    up = np.asarray(up, dtype=float)
    down = np.asarray(down, dtype=float)
    m = labels != "none"
    denom = np.where((up[m] + down[m]) == 0, 1.0, up[m] + down[m])
    dir_score = up[m] / denom
    conf = (dir_score >= dir_hi) | (dir_score <= dir_lo)
    call_up = dir_score >= dir_hi
    true_up = labels[m] == "up"
    wrong = conf & (call_up != true_up)
    return pd.DataFrame(
        {
            "label": labels[m],
            "dir_score": dir_score,
            "confident": conf,
            "wrong": wrong,
        }
    )
