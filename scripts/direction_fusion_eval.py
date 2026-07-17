"""Goal 2: N-way direction fusion on OOD-val — 2-way (GO+neighbour) vs 3-way (+embedding).

Builds each direction channel's ``r`` on the dual-OOD val partition and runs them
through ``fuse_direction_channels`` (CFA-gate each, rank-fuse survivors, model DE
kept). Reports mean(AUROC_de, AUROC_dir) for baseline (two-stage alone), 2-way
(+neighbour), and — when a gene-embeddings cache is present — 3-way (+embedding).
The embedding channel is skipped (with a note) if its cache is absent, so the 2-way
validation runs fully offline.

Run: uv run --group eval python scripts/direction_fusion_eval.py
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
from bio_reasoning.features.neighbor_retrieval import build_neighbor_graph, neighbor_channel
from bio_reasoning.models.direction_fusion import fuse_direction_channels
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
STRING_CACHE = str(_DATA / "external/string_partners_universe.json")
EMB_CACHE = str(_DATA / "external/gene_embeddings.json")


def _channels(df, partners, seed):
    tr, va = holdout_split(df, seed=seed, pert_frac=0.4, gene_frac=0.4)
    train, val = df.iloc[tr], df.iloc[va].reset_index(drop=True)
    model = TwoStageDEDIR(featurizer=GoPairFeaturizer(PERT_CACHE, GENE_CACHE)).fit(
        train.pert.tolist(), train.gene.tolist(), train.label.to_numpy()
    )
    up, down = model.predict(val.pert.tolist(), val.gene.tolist())
    s_de = up + down
    r_go = np.divide(up, s_de, out=np.full_like(up, 0.5), where=s_de > 0)

    pnb, gnb = build_neighbor_graph(val[["pert", "gene"]].astype(str), partners, train)
    nb = neighbor_channel(val[["pert", "gene"]].astype(str), train, pnb, gnb, min_support=3)

    cands = [("neighbour", nb.r)]
    if os.path.exists(EMB_CACHE):
        from bio_reasoning.features.gene_embeddings import (
            build_gene_text,
            fit_direction_ridge,
            gene_embedding_channel,
            load_gene_embeddings,
        )

        syms = sorted(set(df.pert.astype(str)) | set(df.gene.astype(str)))
        text = build_gene_text(syms, GENE_CACHE)
        emb = load_gene_embeddings(text, EMB_CACHE)  # offline: cache hit
        ridge = fit_direction_ridge(train, emb)
        cands.append(("embedding", gene_embedding_channel(val[["pert", "gene"]], ridge, emb).r))

    return val.label.to_numpy(), s_de, r_go, up, down, cands


def main() -> None:
    df = pd.read_csv(TRAIN)
    with open(STRING_CACHE) as f:
        partners = {k: set(v) for k, v in json.load(f).items()}
    has_emb = os.path.exists(EMB_CACHE)
    print(
        f"embedding channel: {'INCLUDED' if has_emb else 'SKIPPED (no cache — needs OpenAI API)'}"
    )
    print("seed | base | 2-way(+nb) | Δ | 3-way(+emb) | Δ", flush=True)
    b2, b3 = [], []
    for s in range(5):
        labels, s_de, r_go, up, down, cands = _channels(df, partners, s)
        base = evaluate(labels, up, down)["mean"]
        u2, d2, _ = fuse_direction_channels(s_de, r_go, cands[:1], labels)
        m2 = evaluate(labels, u2, d2)["mean"]
        b2.append(m2 - base)
        row = f"  {s}  | {base:.3f} | {m2:.3f} | {m2 - base:+.3f}"
        if has_emb:
            u3, d3, _ = fuse_direction_channels(s_de, r_go, cands, labels)
            m3 = evaluate(labels, u3, d3)["mean"]
            b3.append(m3 - base)
            row += f" | {m3:.3f} | {m3 - base:+.3f}"
        print(row, flush=True)
    print(f"\n2-way Δmean: {np.mean(b2):+.3f} ± {np.std(b2):.3f}", flush=True)
    if b3:
        print(f"3-way Δmean: {np.mean(b3):+.3f} ± {np.std(b3):.3f}", flush=True)


if __name__ == "__main__":
    main()
