"""Apply the floor-to-prior transform to an already-saved Track B submission.

Post-processes a submission CSV: any row whose ``(prediction_up,
prediction_down)`` is a zero-signal ``(0, 0)`` tie is replaced with the
perturbation's graded category prior (``direction_prior.prior_scores``). This
is the PR #13 fix applied offline — no agent inference — so a submission that
already cost real tokens can be corrected and re-scored/re-submitted for ~$0.

Usage:
    uv run --group track-b python scripts/apply_floor_to_prior.py \\
        --in  mb/findings/solutions/track-b-agentic-LB0.488000.csv \\
        --test data/raw/track_a/test.csv \\
        --out outputs/track_b/floored/submission.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from tools.direction_prior import floor_to_prior

ROOT = Path(__file__).resolve().parents[1]


def apply_floor(sub: pd.DataFrame, id_to_pert: dict[str, str]) -> tuple[pd.DataFrame, int]:
    """Return (floored submission, n_rows_floored). Perts resolved by row id."""
    out = sub.copy()
    n_floored = 0
    ups, downs = [], []
    for _, r in sub.iterrows():
        up, down = float(r["prediction_up"]), float(r["prediction_down"])
        pert = id_to_pert[r["id"]]
        new_up, new_down = floor_to_prior(up, down, pert)
        if (new_up, new_down) != (up, down):
            n_floored += 1
        ups.append(new_up)
        downs.append(new_down)
    out["prediction_up"] = ups
    out["prediction_down"] = downs
    return out, n_floored


def _direction_counts(df: pd.DataFrame) -> dict[str, int]:
    up = df["prediction_up"].to_numpy(dtype=float)
    dn = df["prediction_down"].to_numpy(dtype=float)
    return {
        "up>down": int((up > dn).sum()),
        "down>up": int((dn > up).sum()),
        "tie(0,0)": int(((up == 0.0) & (dn == 0.0)).sum()),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--in", dest="in_csv", type=Path, required=True)
    p.add_argument("--test", type=Path, default=ROOT / "data/raw/track_a/test.csv")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    sub = pd.read_csv(args.in_csv)
    test = pd.read_csv(args.test)
    id_to_pert = dict(zip(test["id"].astype(str), test["pert"].astype(str), strict=False))

    before = _direction_counts(sub)
    floored, n_floored = apply_floor(sub, id_to_pert)
    after = _direction_counts(floored)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    floored.to_csv(args.out, index=False)

    n = len(sub)
    print(f"Rows: {n}  |  floored (0,0)->prior: {n_floored} ({100 * n_floored / n:.0f}%)")
    print(f"Before: {before}")
    print(f"After:  {after}")
    print(f"Remaining (0,0) ties: {after['tie(0,0)']} (expected 0)")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
