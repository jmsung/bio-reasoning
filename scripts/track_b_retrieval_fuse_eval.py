"""Score the retrieval agent's DE ⊕ neighbour-retrieval DIR fusion on the labelled holdout.

The retrieval agent is strong-DE / weak-DIR; the incumbent neighbour-retrieval
channel is a strong DIR lever (findings/neighbor-retrieval-direction-lever). This
fuses the agent's DE *magnitude* (``up + down``) with the neighbour channel's
direction via ``fuse_neighbour_direction`` (metric math: up=DE*r, down=DE*(1-r)),
keeping the agent's DE ranking untouched, and scores agent-only vs fused on the
same dual-OOD holdout the agent was evaluated on — so we know the expected LB
before submitting.

Reads a per-row eval dump written by ``track_b_retrieval_agent.py --eval --out``
(columns: pert, gene, label, up, down); rebuilds the dual-OOD holdout at the same
fold-seed and asserts the dump aligns to it. Offline (STRING partners cached).

Usage:
    uv run --group eval python scripts/track_b_retrieval_fuse_eval.py \\
        --dump submissions/eval_dump_seed0.csv --fold-seed 0
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from bio_reasoning.eval.split import assert_leak_free, holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.features.neighbor_retrieval import build_neighbor_graph, fuse_neighbour_direction
from bio_reasoning.features.string_graph import fetch_string_partners

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
STRING_CACHE = ROOT / "data/external/string_partners_universe.json"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dump", type=Path, required=True, help="per-row eval dump from --eval --out")
    ap.add_argument("--fold-seed", type=int, default=0)
    ap.add_argument("--weight", type=float, default=0.5, help="neighbour direction share [0,1]")
    ap.add_argument("--min-support", type=int, default=3)
    args = ap.parse_args()

    train_full = pd.read_csv(TRAIN)
    tr_idx, ev_idx = holdout_split(train_full, seed=args.fold_seed)
    assert_leak_free(train_full, tr_idx, ev_idx)
    tr = train_full.iloc[tr_idx].reset_index(drop=True)
    ev = train_full.iloc[ev_idx].reset_index(drop=True)

    dump = pd.read_csv(args.dump)
    ev = ev.head(len(dump)).reset_index(drop=True)
    # The dump is ev.head(N) in order; assert the (pert, gene) keys line up.
    assert (
        ev["pert"].astype(str).to_numpy() == dump["pert"].astype(str).to_numpy()
    ).all(), "pert misalignment between dump and rebuilt holdout"
    assert (
        ev["gene"].astype(str).to_numpy() == dump["gene"].astype(str).to_numpy()
    ).all(), "gene misalignment between dump and rebuilt holdout"

    labels = ev["label"].astype(str).to_numpy()
    agent_up = dump["up"].to_numpy(dtype=float)
    agent_down = dump["down"].to_numpy(dtype=float)

    syms = sorted(
        set(tr["pert"].astype(str))
        | set(tr["gene"].astype(str))
        | set(ev["pert"].astype(str))
        | set(ev["gene"].astype(str))
    )
    partners = fetch_string_partners(syms, STRING_CACHE)

    q = ev[["pert", "gene"]].astype(str).reset_index(drop=True)
    pnb, gnb = build_neighbor_graph(q, partners, tr)
    fused_up, fused_down, covered = fuse_neighbour_direction(
        q, agent_up, agent_down, tr, pnb, gnb, min_support=args.min_support, weight=args.weight
    )

    s_agent = evaluate(labels, agent_up, agent_down)
    s_fused = evaluate(labels, fused_up, fused_down)

    print(f"holdout fold-seed={args.fold_seed}, N={len(ev)} rows")
    print(f"neighbour DIR coverage: {covered.mean():.1%}")
    print("\n=== agent standalone ===")
    print(
        f"  mean={s_agent['mean']:.3f} (de={s_agent['auroc_de']:.3f}, dir={s_agent['auroc_dir']:.3f})"
    )
    print("=== agent DE  neighbour DIR (fused) ===")
    print(
        f"  mean={s_fused['mean']:.3f} (de={s_fused['auroc_de']:.3f}, dir={s_fused['auroc_dir']:.3f})"
    )
    print("\n  incumbent Track B LB = 0.597")


if __name__ == "__main__":
    main()
