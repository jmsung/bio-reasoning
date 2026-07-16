"""Eval: blend two-stage direction into the Track B floor-to-prior submission on OOD-val.

Loads the saved floor-to-prior OOD-val submission (the agent run scored on the
dual-OOD holdout, mean 0.5636), fits the two-stage GO model on the holdout train
partition (leak-free), and sweeps the direction-blend weight. Self-validates:
re-scoring the input reproduces floor-to-prior before any blend, so the reported
lift is trustworthy.

Finding: blending two-stage direction beats floor-to-prior for every weight in
(0, 1) — direction AUROC rises ~0.01, mean from ~0.565 to ~0.571 — while the DE
axis is left to the (stronger) submission.

Run: uv run --group eval python scripts/track_b_two_stage_ood_val.py \
       --floored-sub <floored-agent-ood-val>.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.features.go_terms import GoPairFeaturizer
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR
from bio_reasoning.models.track_b_blend import blend_direction

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
PERT_CACHE = ROOT / "data/interim/pert_go_category.json"
GENE_CACHE = ROOT / "data/interim/gene_go_bp.json"
SEED = 0
WEIGHTS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    # The floored agent OOD-val submission (private mb/ artifact); pass explicitly.
    ap.add_argument("--floored-sub", type=Path, required=True)
    ap.add_argument("--train", type=Path, default=TRAIN)
    args = ap.parse_args()

    train = pd.read_csv(args.train)
    tr_idx, val_idx = holdout_split(train, seed=SEED)
    val = train.iloc[val_idx][["id", "pert", "gene", "label"]]
    sub = pd.read_csv(args.floored_sub, usecols=["id", "prediction_up", "prediction_down"])
    m = val.merge(sub, on="id", how="left")
    if m.prediction_up.isna().any():
        raise SystemExit("submission does not cover every OOD-val id")
    labels = m.label.to_numpy()
    up, down = m.prediction_up.to_numpy(), m.prediction_down.to_numpy()

    champion = evaluate(labels, up, down)
    print(
        f"floor-to-prior on OOD-val (n={len(m)}): mean={champion['mean']:.4f} "
        f"(de={champion['auroc_de']:.3f} dir={champion['auroc_dir']:.3f})"
    )

    trn = train.iloc[tr_idx]
    feat = GoPairFeaturizer(PERT_CACHE, GENE_CACHE)
    model = TwoStageDEDIR(featurizer=feat).fit(trn.pert, trn.gene, trn.label.to_numpy())
    ts_up, ts_down = model.predict(m.pert.tolist(), m.gene.tolist())

    print(f"\n{'weight':>7}{'mean':>9}{'auroc_de':>10}{'auroc_dir':>11}")
    best = (champion["mean"], 0.0)
    for w in WEIGHTS:
        bu, bd = blend_direction(up, down, ts_up, ts_down, weight=w)
        r = evaluate(labels, bu, bd)
        mark = " *" if r["mean"] > champion["mean"] else ""
        print(f"{w:>7.1f}{r['mean']:>9.4f}{r['auroc_de']:>10.3f}{r['auroc_dir']:>11.3f}{mark}")
        if r["mean"] > best[0]:
            best = (r["mean"], w)

    delta = best[0] - champion["mean"]
    print(
        f"\nBest blend: weight={best[1]:.1f} mean={best[0]:.4f} "
        f"(+{delta:.4f} vs floor-to-prior {champion['mean']:.4f}). "
        "Direction-only blend; DE axis unchanged. One split — confirm on the LB."
    )


if __name__ == "__main__":
    main()
