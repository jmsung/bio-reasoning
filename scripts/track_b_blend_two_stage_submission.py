"""Blend two-stage direction into a saved Track B submission (offline, ~$0).

Post-processes a Track B submission: keeps every row's DE magnitude
(``up + down``) and metadata (reasoning trace, tokens, …) but rank-blends the
two-stage GO model's direction into ``up / (up + down)``. On the dual-OOD val
split this lifts floor-to-prior ~0.565 → ~0.571
(`scripts/track_b_two_stage_ood_val.py`). The two-stage model is fit on all of
train and predicts the submission's (pert, gene) pairs, resolved via the test
file. No agent inference — a submission that already cost tokens is improved for
free.

Usage:
    uv run --group eval python scripts/track_b_blend_two_stage_submission.py \\
        --in  <floored-track-b-submission>.csv \\
        --out submissions/track_b_blend_two_stage.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from bio_reasoning.features.go_terms import GoPairFeaturizer
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR
from bio_reasoning.models.track_b_blend import blend_direction

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
TEST = ROOT / "data/raw/track_a/test.csv"
PERT_CACHE = ROOT / "data/interim/pert_go_category.json"
GENE_CACHE = ROOT / "data/interim/gene_go_bp.json"


def blend_submission(
    sub: pd.DataFrame, test: pd.DataFrame, train: pd.DataFrame, featurizer, weight: float
) -> pd.DataFrame:
    """Return ``sub`` with prediction_up/down direction-blended; other columns kept."""
    id_pair = test.set_index("id")[["pert", "gene"]]
    missing = set(sub.id) - set(id_pair.index)
    if missing:
        raise KeyError(
            f"{len(missing)} submission ids absent from test file, e.g. {list(missing)[:3]}"
        )
    perts = id_pair.loc[sub.id, "pert"].tolist()
    genes = id_pair.loc[sub.id, "gene"].tolist()

    model = TwoStageDEDIR(featurizer=featurizer).fit(
        train.pert.tolist(), train.gene.tolist(), train.label.to_numpy()
    )
    ts_up, ts_down = model.predict(perts, genes)
    new_up, new_down = blend_direction(
        sub.prediction_up.to_numpy(), sub.prediction_down.to_numpy(), ts_up, ts_down, weight=weight
    )
    out = sub.copy()
    out["prediction_up"] = new_up
    out["prediction_down"] = new_down
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="in_csv", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=ROOT / "submissions/track_b_blend_two_stage.csv")
    ap.add_argument("--test", type=Path, default=TEST)
    ap.add_argument("--weight", type=float, default=0.5, help="two-stage direction weight in [0,1]")
    args = ap.parse_args()

    sub = pd.read_csv(args.in_csv)
    test = pd.read_csv(args.test)
    train = pd.read_csv(TRAIN)
    featurizer = GoPairFeaturizer(PERT_CACHE, GENE_CACHE)
    out = blend_submission(sub, test, train, featurizer, args.weight)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"wrote {args.out}  ({len(out)} rows, weight={args.weight})")


if __name__ == "__main__":
    main()
