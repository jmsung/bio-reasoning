"""Eval: neighbour-direction fusion on the Track B floored submission, OOD-val.

Loads the saved floor-to-prior OOD-val submission (mean ~0.565), fits the STRING
neighbour graph on the holdout TRAIN partition (leak-free), and fuses the
neighbour direction into the floored base via ``fuse_neighbour_direction`` — the
#28 Track A lever, applied to Track B. Track B keeps the default fusion ``weight``
(0.5, unswept — PR #31 found the neighbour-vs-base weight a flat lever, +0.004
within seed noise). Reports mean + DE/DIR per axis vs the live floored base and the
current Track B best (dir-blend 0.5712 / LB 0.578).

Run: uv run --group eval python scripts/track_b_de_dir_ood_val.py \\
       --floored-sub <floored-agent-ood-val>.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.features.neighbor_retrieval import build_neighbor_graph, fuse_neighbour_direction
from bio_reasoning.features.string_graph import fetch_string_partners

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
STRING_CACHE = ROOT / "data/external/string_partners_universe.json"
SEED = 0
DIRBLEND_BEST = 0.5712  # current Track B best (dir-blend w=0.7, LB 0.578)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--floored-sub", type=Path, required=True)
    ap.add_argument("--train", type=Path, default=TRAIN)
    args = ap.parse_args()

    df = pd.read_csv(args.train)
    tr_idx, val_idx = holdout_split(df, seed=SEED)
    train, val = df.iloc[tr_idx], df.iloc[val_idx][["id", "pert", "gene", "label"]].reset_index(
        drop=True
    )
    sub = pd.read_csv(args.floored_sub, usecols=["id", "prediction_up", "prediction_down"])
    m = val.merge(sub, on="id", how="left")
    if m.prediction_up.isna().any():
        raise SystemExit("floored submission does not cover every OOD-val id")
    labels = m.label.to_numpy()

    base = evaluate(labels, m.prediction_up.to_numpy(), m.prediction_down.to_numpy())
    print(
        f"floored base on OOD-val (n={len(m)}): mean={base['mean']:.4f} "
        f"(de={base['auroc_de']:.3f} dir={base['auroc_dir']:.3f})"
    )

    syms = sorted(set(df.pert.astype(str)) | set(df.gene.astype(str)))
    partners = fetch_string_partners(syms, STRING_CACHE)
    q = m[["pert", "gene"]].astype(str)
    pnb, gnb = build_neighbor_graph(q, partners, train)
    fu, fd, covered = fuse_neighbour_direction(
        q, m.prediction_up.to_numpy(), m.prediction_down.to_numpy(), train, pnb, gnb, min_support=3
    )
    fused = evaluate(labels, fu, fd)
    print(
        f"neighbour-fused on OOD-val: mean={fused['mean']:.4f} "
        f"(de={fused['auroc_de']:.3f} dir={fused['auroc_dir']:.3f}) | coverage {covered.mean():.0%}"
    )
    print(
        f"\nΔ vs floored base {base['mean']:.4f}: {fused['mean'] - base['mean']:+.4f} | "
        f"Δ vs dir-blend best {DIRBLEND_BEST}: {fused['mean'] - DIRBLEND_BEST:+.4f}"
    )
    verdict = "BEATS" if fused["mean"] > DIRBLEND_BEST else "does NOT beat"
    print(f"neighbour-direction fusion {verdict} the current Track B best on this OOD-val split.")


if __name__ == "__main__":
    main()
