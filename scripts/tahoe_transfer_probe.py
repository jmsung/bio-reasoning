"""Does Tahoe-100M add any signal to Track A? Feasibility + perfect-oracle upper bound.

Tahoe is a drug-perturbation cancer-cell atlas; Track A is genetic CRISPRi in mouse
macrophages. The only leak-free channel is drug-MoA: a Tahoe drug that inhibits pert
gene X proxies "knocking down X". This probe measures, on the honest dual-OOD split:

1. **Coverage** — what fraction of Track A perts/rows can the drug-MoA channel score
   at all (a pert is scorable iff some Tahoe drug targets it)?
2. **Perfect-oracle upper bound** — give the covered rows their *true* DE + direction
   (the best any Tahoe drug-MoA channel could achieve) and fuse into the incumbent
   (two-stage GO x DIR + neighbour-DIR). If even this perfect oracle cannot lift the
   mean-AUROC above seed noise, the real (mismatched, noisy) channel cannot either.

Fully offline: needs only ``data/external/tahoe_drug_targets.json`` (from
``fetch_tahoe_drug_targets.py``) + Track A train. No Tahoe pseudobulk download.

Run: ``uv run python scripts/tahoe_transfer_probe.py``.
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
from bio_reasoning.features.tahoe_transfer import (
    coverage_report,
    load_drug_targets,
    perfect_oracle_channel,
)
from bio_reasoning.models.fuse import Channel, fuse
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR

_ROOT = Path(__file__).resolve().parents[1]
_local = _ROOT / "data"
_DATA = (
    _local if (_local / "raw" / "track_a" / "train.csv").exists() else _ROOT.parent / "cb" / "data"
)
TRAIN = os.getenv("BIOREASONING_TRAIN_CSV") or str(_DATA / "raw" / "track_a" / "train.csv")
PERT_CACHE = str(_DATA / "interim" / "pert_go_category.json")
GENE_CACHE = str(_DATA / "interim" / "gene_go_bp.json")
UNIVERSE = str(_DATA / "external" / "string_partners_universe.json")
DRUG_TARGETS = str(_DATA / "external" / "tahoe_drug_targets.json")


def _incumbent_and_oracle(df, partners, drug_targets, seed):
    tr, va = holdout_split(df, seed=seed, pert_frac=0.4, gene_frac=0.4)
    train, val = df.iloc[tr], df.iloc[va].reset_index(drop=True)
    labels = val["label"].to_numpy()

    # incumbent: two-stage GO x DIR + neighbour-DIR (the live direction stack)
    model = TwoStageDEDIR(featurizer=GoPairFeaturizer(PERT_CACHE, GENE_CACHE))
    model.fit(train["pert"], train["gene"], train["label"])
    up, down = model.predict(val["pert"], val["gene"])
    cur_s = up + down
    cur_r = np.divide(up, cur_s, out=np.full_like(up, 0.5), where=cur_s > 0)

    tp, tg = set(train["pert"].astype(str)), set(train["gene"].astype(str))
    pnb = {p: partners.get(p, set()) & tp for p in val["pert"].astype(str).unique()}
    gnb = {g: partners.get(g, set()) & tg for g in val["gene"].astype(str).unique()}
    nb = neighbor_channel(val[["pert", "gene"]].astype(str), train, pnb, gnb, min_support=3)

    base_channels = [Channel("model", s_de=cur_s, r=cur_r), Channel("neighbour", s_de=None, r=nb.r)]
    bu, bd = fuse(base_channels)
    base = evaluate(labels, bu, bd)

    # + perfect Tahoe oracle (true DE/dir on drug-MoA-covered rows only)
    oracle, covered = perfect_oracle_channel(val[["pert", "gene"]], labels, drug_targets)
    fu, fd = fuse(base_channels + [oracle])
    fused = evaluate(labels, fu, fd)
    return base, fused, int(covered.sum()), len(val)


def main() -> None:
    df = pd.read_csv(TRAIN)
    partners = {k: set(v) for k, v in json.load(open(UNIVERSE)).items()}
    drug_targets = load_drug_targets(DRUG_TARGETS)

    print("=== Drug-MoA coverage of Track A (the feasibility crux) ===", flush=True)
    for name, sub in (("train", df),):
        rep = coverage_report(sub, drug_targets)
        print(
            f"  {name}: {rep['n_perts_covered']}/{rep['n_perts']} perts "
            f"({rep['pert_coverage'] * 100:.1f}%), "
            f"{rep['n_rows_covered']}/{rep['n_rows']} rows "
            f"({rep['row_coverage'] * 100:.1f}%)",
            flush=True,
        )
        print(f"  covered perts: {rep['covered_perts']}", flush=True)

    print(
        "\n=== Perfect-Tahoe-oracle upper bound on dual-OOD val (5 seeds) ===\n"
        "seed | val_cov | base(de/dir/mean) | +oracle(de/dir/mean) | Δmean",
        flush=True,
    )
    dmeans = []
    for s in range(5):
        b, f, ncov, nval = _incumbent_and_oracle(df, partners, drug_targets, s)
        dm = f["mean"] - b["mean"]
        dmeans.append(dm)
        print(
            f"  {s}  | {ncov:3d}/{nval} | "
            f"{b['auroc_de']:.3f}/{b['auroc_dir']:.3f}/{b['mean']:.3f} | "
            f"{f['auroc_de']:.3f}/{f['auroc_dir']:.3f}/{f['mean']:.3f} | {dm:+.4f}",
            flush=True,
        )
    print(
        f"\nΔmean over 5 seeds (PERFECT oracle, upper bound): "
        f"{np.mean(dmeans):+.4f} ± {np.std(dmeans):.4f}\n"
        "The real drug-MoA channel does strictly worse (drug!=knockdown, "
        "cancer!=macrophage, selection inflation).",
        flush=True,
    )


if __name__ == "__main__":
    main()
