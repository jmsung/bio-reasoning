"""CollecTRI TF-regulon coverage on the dual-OOD val split (caps the DE lift).

Fetches + caches signed mouse CollecTRI edges, then reports how much of the
held-out OOD-val rows the regulon can score: fraction whose pert is a covered TF,
fraction that are actual regulon edges, and the edge fraction among TF-pert rows.
Coverage is the ceiling on achievable DE lift — measure it before spending a
Kaggle submission (`mb/notes/rank1-plan.md`).

Run: uv run --group network --group eval python scripts/tf_regulon_coverage.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.features.tf_regulon import (
    TFRegulonFeaturizer,
    coverage_report,
    load_collectri_edges,
)

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
CACHE = ROOT / "data/external/collectri_mouse.csv"
SEED = 0


def main() -> None:
    edges = load_collectri_edges(CACHE, organism="mouse")
    feat = TFRegulonFeaturizer(edges)
    print(f"CollecTRI mouse: {len(edges)} edges, {edges.source.nunique()} TFs -> {CACHE}")

    df = pd.read_csv(TRAIN)
    _, val = holdout_split(df, seed=SEED)
    val_df = df.iloc[val]

    for name, d in [("full train", df), ("dual-OOD val", val_df)]:
        rep = coverage_report(feat, d.pert.tolist(), d.gene.tolist())
        print(
            f"\n== {name} ({int(rep['n'])} rows) ==\n"
            f"  TF-pert coverage : {rep['tf_covered_frac']:.3f}\n"
            f"  regulon-edge rows: {rep['edge_frac']:.3f}\n"
            f"  edges | TF-pert  : {rep['edge_among_tf_frac']:.3f}"
        )


if __name__ == "__main__":
    main()
