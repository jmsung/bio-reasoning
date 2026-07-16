"""Sweep the blend α on a saved OOD-val submission — offline, no agent inference.

For each α in [0, 1], scores ``α·saved + (1−α)·prior`` on the dual-OOD val split
(`holdout_split`) and prints the metric, so α can be tuned for ``--blend-alpha``
without re-running the agent. The saved predictions must be OOD-val predictions
(built from `holdout_split` on TRAIN with the same seed).

Usage:
    uv run --group eval python scripts/sweep_blend_alpha.py \\
        --preds mb/findings/solutions/track-b-floor-to-prior-OODval0.563607.csv \\
        --train data/raw/track_a/train.csv --seed 0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from tools.direction_prior import prior_scores  # noqa: E402

from bio_reasoning.eval.split import holdout_split  # noqa: E402
from bio_reasoning.eval.track_a_score import score_preds  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--preds", type=Path, required=True, help="Saved OOD-val submission CSV.")
    p.add_argument("--train", type=Path, default=ROOT / "data/raw/track_a/train.csv")
    p.add_argument("--seed", type=int, default=0, help="holdout_split seed (must match the run).")
    args = p.parse_args()

    tr = pd.read_csv(args.train)
    _, ev_idx = holdout_split(tr, seed=args.seed)
    val = tr.iloc[ev_idx].reset_index(drop=True)
    val["id"] = val["pert"].astype(str) + "_" + val["gene"].astype(str)

    sub = pd.read_csv(args.preds)
    m = val.merge(sub[["id", "prediction_up", "prediction_down"]], on="id", how="inner")
    if len(m) == 0:
        p.error("No id overlap between --preds and the holdout val split (seed mismatch?).")

    labels = m["label"].astype(str).to_numpy()
    a_up = m["prediction_up"].to_numpy(dtype=float)
    a_down = m["prediction_down"].to_numpy(dtype=float)
    uniq = {g: prior_scores(g) for g in m["pert"].unique()}
    p_up = np.array([uniq[g][0] for g in m["pert"]])
    p_down = np.array([uniq[g][1] for g in m["pert"]])

    print(f"aligned {len(m)} OOD-val rows (seed {args.seed})")
    print(f"  saved (α=1): {score_preds(labels, a_up, a_down)['mean']:.4f}")
    print(f"  pure prior (α=0): {score_preds(labels, p_up, p_down)['mean']:.4f}")
    best = (1.0, -1.0)
    for a in (i / 10 for i in range(11)):
        mean = score_preds(labels, a * a_up + (1 - a) * p_up, a * a_down + (1 - a) * p_down)["mean"]
        best = max(best, (a, mean), key=lambda t: t[1])
        print(f"  α={a:.1f}: {mean:.4f}")
    print(f"BEST α={best[0]:.1f} → {best[1]:.4f}")


if __name__ == "__main__":
    main()
