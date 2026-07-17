"""Goal 1: sweep the neighbour-vs-model direction blend weight on OOD-val.

Baseline = two-stage GO model. Candidate = keep its DE, fuse its direction `r` with
the neighbour channel's `r` at weight `w` on the neighbour side (`1-w` on the model).
`w=0.5` is the equal-weight fusion that scored the +0.027 / LB-0.585 result. Reports
mean(AUROC_de, AUROC_dir) vs `w` over seeds 0-4 and picks the OOD-val argmax.

Run: uv run --group eval python scripts/de_dir_weight_sweep.py
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.features.go_terms import GoPairFeaturizer
from bio_reasoning.features.neighbor_retrieval import build_neighbor_graph, neighbor_channel
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
CACHE = str(_DATA / "external/string_partners_universe.json")
WEIGHTS = [0.0, 0.25, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 1.0]


def _fetch(syms: list[str]) -> dict[str, set[str]]:
    if os.path.exists(CACHE):
        return {k: set(v) for k, v in json.load(open(CACHE)).items()}
    base = "https://string-db.org/api/json/interaction_partners"
    out: dict[str, set[str]] = {}
    for i in range(0, len(syms), 60):
        data = urllib.parse.urlencode(
            {"identifiers": "\n".join(syms[i : i + 60]), "species": 10090, "limit": 500}
        ).encode()
        try:
            with urllib.request.urlopen(urllib.request.Request(base, data=data), timeout=90) as r:
                rows = json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            print("fetch err", i, repr(e), flush=True)
            rows = []
        for row in rows:
            out.setdefault(row["preferredName_A"], set()).add(row["preferredName_B"])
        time.sleep(1)
    os.makedirs("data/external", exist_ok=True)
    json.dump({k: sorted(v) for k, v in out.items()}, open(CACHE, "w"))
    return out


def _seed_means(df, partners, seed):
    tr, va = holdout_split(df, seed=seed, pert_frac=0.4, gene_frac=0.4)
    train, val = df.iloc[tr], df.iloc[va].reset_index(drop=True)
    model = TwoStageDEDIR(featurizer=GoPairFeaturizer(PERT_CACHE, GENE_CACHE)).fit(
        train.pert.tolist(), train.gene.tolist(), train.label.to_numpy()
    )
    up, down = model.predict(val.pert.tolist(), val.gene.tolist())
    s_de = up + down
    r = np.divide(up, s_de, out=np.full_like(up, 0.5), where=s_de > 0)
    pnb, gnb = build_neighbor_graph(val[["pert", "gene"]].astype(str), partners, train)
    nb = neighbor_channel(val[["pert", "gene"]].astype(str), train, pnb, gnb, min_support=3)
    labels = val.label.to_numpy()
    means = {}
    for w in WEIGHTS:
        fu, fd = fuse(
            [Channel("model", s_de=s_de, r=r), Channel("neighbour", s_de=None, r=nb.r)],
            weights=[1 - w, w],
        )
        means[w] = evaluate(labels, fu, fd)["mean"]
    return means


def main() -> None:
    df = pd.read_csv(TRAIN)
    syms = sorted(set(df.pert.astype(str)) | set(df.gene.astype(str)))
    partners = _fetch(syms)
    rows = [_seed_means(df, partners, s) for s in range(5)]
    print("w    | mean per seed 0..4            | mean±std", flush=True)
    best_w, best_mean = None, -1.0
    for w in WEIGHTS:
        vals = [r[w] for r in rows]
        m = float(np.mean(vals))
        print(
            f"{w:<4} | {' '.join(f'{v:.3f}' for v in vals)} | {m:.3f} ± {np.std(vals):.3f}",
            flush=True,
        )
        if m > best_mean:
            best_w, best_mean = w, m
    print(
        f"\nargmax w = {best_w}  (mean {best_mean:.3f});  w=0.5 baseline = {np.mean([r[0.5] for r in rows]):.3f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
