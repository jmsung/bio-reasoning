"""Fuse the neighbour direction into a saved Track B submission (offline, ~$0).

Track-B parity with the #28 Track A win (LB 0.585): keep the Track B floored
submission's DE ranking and metadata (reasoning trace, tokens, …) but rank-fuse
the STRING-neighbour-retrieval direction into ``up/(up+down)`` via
``fuse_neighbour_direction`` — the same lever, applied to the floored base instead
of the two-stage model. STRING partners for train+test symbols are fetched from
string-db.org (mouse) on first run and cached. No agent inference.

Usage:
    uv run --group eval python scripts/track_b_de_dir_submission.py \\
        --in  <floored-track-b-submission>.csv \\
        --out submissions/track_b_de_dir.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from bio_reasoning.features.neighbor_retrieval import build_neighbor_graph, fuse_neighbour_direction
from bio_reasoning.features.string_graph import fetch_string_partners

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
TEST = ROOT / "data/raw/track_a/test.csv"
STRING_CACHE = ROOT / "data/external/string_partners_submission.json"
OUT = ROOT / "submissions/track_b_de_dir.csv"


def neighbour_fuse_submission(
    sub: pd.DataFrame, test: pd.DataFrame, train: pd.DataFrame, partners, min_support: int = 3
) -> pd.DataFrame:
    """Return ``sub`` with prediction_up/down neighbour-direction-fused; metadata kept."""
    id_pair = test.set_index("id")[["pert", "gene"]].astype(str)
    missing = set(sub.id) - set(id_pair.index)
    if missing:
        raise KeyError(f"{len(missing)} submission ids absent from test, e.g. {list(missing)[:3]}")
    q = id_pair.loc[sub.id].reset_index(drop=True)

    pnb, gnb = build_neighbor_graph(q, partners, train)
    up, down, covered = fuse_neighbour_direction(
        q,
        sub.prediction_up.to_numpy(),
        sub.prediction_down.to_numpy(),
        train,
        pnb,
        gnb,
        min_support,
    )
    print(f"neighbour direction coverage on test: {covered.mean():.1%}", flush=True)
    out = sub.copy()
    out["prediction_up"] = up
    out["prediction_down"] = down
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="in_csv", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--test", type=Path, default=TEST)
    args = ap.parse_args()

    sub = pd.read_csv(args.in_csv)
    test = pd.read_csv(args.test)
    train = pd.read_csv(TRAIN)
    syms = sorted(
        set(train.pert.astype(str))
        | set(train.gene.astype(str))
        | set(test.pert.astype(str))
        | set(test.gene.astype(str))
    )
    partners = fetch_string_partners(syms, STRING_CACHE)
    out = neighbour_fuse_submission(sub, test, train, partners)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"wrote {args.out}  ({len(out)} rows)", flush=True)


if __name__ == "__main__":
    main()
