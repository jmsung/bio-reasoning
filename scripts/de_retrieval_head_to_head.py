"""Goal 4: does fusing the neighbour-retrieval direction into the two-stage GO
model lift the mean(AUROC_de, AUROC_dir) metric on OOD-val?

Baseline = two-stage GO×DIR model alone. Candidate = keep its DE score, fuse its
direction `r` with the neighbour channel's `r` via the merged `fuse()` harness
(uncovered rows fall back to the model's direction). Reports both, multi-seed.
Run: `uv run python scripts/de_retrieval_head_to_head.py`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.features.go_terms import GoPairFeaturizer
from bio_reasoning.features.neighbor_retrieval import neighbor_channel
from bio_reasoning.models.fuse import Channel, fuse
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR

_ROOT = Path(__file__).resolve().parents[1]
# A fresh worktree has an empty (gitignored) data/ — fall back to the sibling cb/ checkout.
_local = _ROOT / "data"
_DATA = (
    _local if (_local / "raw" / "track_a" / "train.csv").exists() else _ROOT.parent / "cb" / "data"
)
TRAIN = os.getenv("BIOREASONING_TRAIN_CSV") or str(_DATA / "raw" / "track_a" / "train.csv")
PERT_CACHE = str(_DATA / "interim" / "pert_go_category.json")
GENE_CACHE = str(_DATA / "interim" / "gene_go_bp.json")
UNIVERSE = "data/external/string_partners_universe.json"


def _run(df, partners, seed):
    tr, va = holdout_split(df, seed=seed, pert_frac=0.4, gene_frac=0.4)
    train, val = df.iloc[tr], df.iloc[va].reset_index(drop=True)

    # current best direction model: two-stage GO×DIR
    model = TwoStageDEDIR(featurizer=GoPairFeaturizer(PERT_CACHE, GENE_CACHE))
    model.fit(train["pert"], train["gene"], train["label"])
    up, down = model.predict(val["pert"], val["gene"])
    cur_s = up + down
    cur_r = np.divide(up, cur_s, out=np.full_like(up, 0.5), where=cur_s > 0)

    # neighbour direction channel
    tp, tg = set(train["pert"].astype(str)), set(train["gene"].astype(str))
    pnb = {p: partners.get(p, set()) & tp for p in val["pert"].astype(str).unique()}
    gnb = {g: partners.get(g, set()) & tg for g in val["gene"].astype(str).unique()}
    nb = neighbor_channel(val[["pert", "gene"]].astype(str), train, pnb, gnb, min_support=3)

    labels = val["label"].to_numpy()
    base = evaluate(labels, up, down)

    # fuse: keep two-stage DE, blend direction (neighbour r falls back to model r when uncovered)
    fu, fd = fuse([Channel("model", s_de=cur_s, r=cur_r), Channel("neighbour", s_de=None, r=nb.r)])
    fused = evaluate(labels, fu, fd)
    return base, fused


def main() -> None:
    df = pd.read_csv(TRAIN)
    partners = {k: set(v) for k, v in json.load(open(UNIVERSE)).items()}
    print("seed | base(de/dir/mean) | fused(de/dir/mean) | Δmean", flush=True)
    dmeans = []
    for s in range(5):
        b, f = _run(df, partners, s)
        dm = f["mean"] - b["mean"]
        dmeans.append(dm)
        print(
            f"  {s}  | {b['auroc_de']:.3f}/{b['auroc_dir']:.3f}/{b['mean']:.3f} "
            f"| {f['auroc_de']:.3f}/{f['auroc_dir']:.3f}/{f['mean']:.3f} | {dm:+.3f}",
            flush=True,
        )
    print(f"\nΔmean over 5 seeds: {np.mean(dmeans):+.3f} ± {np.std(dmeans):.3f}", flush=True)


if __name__ == "__main__":
    main()
