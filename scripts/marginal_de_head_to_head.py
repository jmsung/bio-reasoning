"""Goal 3: does fusing the marginal DE channel into the two-stage lift the mean metric?

The marginal channel fails the 0.55 standalone gate (DE-AUROC 0.536) but the
two-stage model's own DE is ~chance (0.50), so a weak-but-real DE signal may still
help when fused. Baseline = two-stage GO model. Candidate = keep its direction, fuse
its DE score with the marginal-degree DE channel via ``fuse()``. Reports
mean(AUROC_de, AUROC_dir) delta over seeds 0-4.

Run: uv run --group eval python scripts/marginal_de_head_to_head.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.features.go_terms import GoPairFeaturizer
from bio_reasoning.features.marginal_properties import marginal_features
from bio_reasoning.models.fuse import Channel, fuse
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR

_ROOT = Path(__file__).resolve().parents[1]
_DATA = (
    _ROOT / "data"
    if (_ROOT / "data/raw/track_a/train.csv").exists()
    else _ROOT.parent / "cb" / "data"
)
TRAIN = str(_DATA / "raw/track_a/train.csv")
PERT_CACHE = str(_DATA / "interim/pert_go_category.json")
GENE_CACHE = str(_DATA / "interim/gene_go_bp.json")
DEGREE_CACHE = str(_DATA / "external/string_degree.json")


def _run(df, degree, seed):
    tr, va = holdout_split(df, seed=seed, pert_frac=0.4, gene_frac=0.4)
    train, val = df.iloc[tr], df.iloc[va].reset_index(drop=True)
    model = TwoStageDEDIR(featurizer=GoPairFeaturizer(PERT_CACHE, GENE_CACHE)).fit(
        train.pert.tolist(), train.gene.tolist(), train.label.to_numpy()
    )
    up, down = model.predict(val.pert.tolist(), val.gene.tolist())
    s_de = up + down
    r = np.divide(up, s_de, out=np.full_like(up, 0.5), where=s_de > 0)

    de_tr = (train.label.to_numpy() != "none").astype(int)
    head = LogisticRegression(max_iter=1000).fit(
        marginal_features(train.pert.tolist(), train.gene.tolist(), degree, log1p=True), de_tr
    )
    s_de_marg = head.predict_proba(
        marginal_features(val.pert.tolist(), val.gene.tolist(), degree, log1p=True)
    )[:, 1]

    labels = val.label.to_numpy()
    base = evaluate(labels, up, down)
    # keep model direction; fuse the DE score with the marginal DE channel
    fu, fd = fuse([Channel("model", s_de=s_de, r=r), Channel("marginal", s_de=s_de_marg, r=None)])
    fused = evaluate(labels, fu, fd)
    return base, fused


def main() -> None:
    df = pd.read_csv(TRAIN)
    with open(DEGREE_CACHE) as _f:
        degree = json.load(_f)
    print("seed | base(de/dir/mean) | fused(de/dir/mean) | Δmean", flush=True)
    dmeans = []
    for s in range(5):
        b, f = _run(df, degree, s)
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
