"""Goal 3: gate + eval the char/prefix family-retrieval channel on OOD-val.

Multi-seed (0-4) on the dual-OOD `holdout_split`, per seed:
  1. incumbent = the now-fixed char n-gram TF-IDF two-stage model (`TwoStageDEDIR`
     + `CharNgramFeaturizer`), fit on the train fold → its `s_de`/`r` on val;
  2. candidate = the family-retrieval channel (`FamilyRetriever`) on val;
  3. standalone family DE-AUROC + DIR-AUROC + coverage;
  4. `cfa_gate` — is the family `s_de` predictive AND diverse vs the incumbent?
  5. fuse(incumbent, family) → mean AUROC vs incumbent-alone and the LB-0.578 mark.

Self-contained: only needs `train.csv` (no STRING/GO fetch). Run:
`uv run --group eval python scripts/family_retrieval_eval.py`.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.features.family_retrieval import FamilyRetriever
from bio_reasoning.features.pair_features import CharNgramFeaturizer
from bio_reasoning.models.fuse import Channel, cfa_gate, fuse
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR

_ROOT = Path(__file__).resolve().parents[1]
TRAIN = os.getenv("BIOREASONING_TRAIN_CSV") or str(_ROOT / "data" / "raw" / "track_a" / "train.csv")
if not os.path.exists(TRAIN):
    TRAIN = str(_ROOT.parent / "cb" / "data" / "raw" / "track_a" / "train.csv")

LB_MARK = 0.578


def _incumbent_channel(train: pd.DataFrame, val: pd.DataFrame) -> Channel:
    """Char n-gram TF-IDF two-stage model, fit on train → (s_de, r) on val."""
    model = TwoStageDEDIR(featurizer=CharNgramFeaturizer())
    model.fit(train["pert"], train["gene"], train["label"])
    up, down = model.predict(val["pert"], val["gene"])
    s_de = up + down
    denom = np.where(s_de == 0, 1.0, s_de)
    return Channel(name="two_stage_char", s_de=s_de, r=up / denom)


def _auroc(y: np.ndarray, score: np.ndarray) -> float:
    ok = np.isfinite(score)
    if ok.sum() < 2 or len(set(y[ok].tolist())) < 2:
        return float("nan")
    return float(roc_auc_score(y[ok], score[ok]))


def _seed_row(df: pd.DataFrame, seed: int) -> dict:
    tr, va = holdout_split(df, seed=seed, pert_frac=0.4, gene_frac=0.4)
    train = df.iloc[tr].reset_index(drop=True)
    val = df.iloc[va].reset_index(drop=True)
    lab = val["label"].to_numpy()
    de_true = (lab != "none").astype(int)

    inc = _incumbent_channel(train, val)
    fam = (
        FamilyRetriever(use_pert=True, use_gene=True, min_support=1)
        .fit(train)
        .channel(val[["pert", "gene"]])
    )

    cov = np.isfinite(fam.s_de)
    de_auroc = _auroc(de_true, fam.s_de)
    dir_mask = np.isfinite(fam.r) & (lab != "none")
    dir_auroc = (
        _auroc((lab[dir_mask] == "up").astype(int), fam.r[dir_mask])
        if dir_mask.sum() >= 2
        else float("nan")
    )
    passed, stats = cfa_gate(fam.s_de, inc.s_de, de_true, min_auroc=0.55, max_abs_corr=0.5)

    inc_up, inc_down = fuse([inc])
    fus_up, fus_down = fuse([inc, fam])
    inc_mean = evaluate(lab, inc_up, inc_down)["mean"]
    fus_mean = evaluate(lab, fus_up, fus_down)["mean"]

    return {
        "seed": seed,
        "cov": float(cov.mean()),
        "de_auroc": de_auroc,
        "dir_auroc": dir_auroc,
        "gate": passed,
        "gate_auroc": stats["auroc"],
        "gate_corr": stats["corr"],
        "inc_mean": inc_mean,
        "fused_mean": fus_mean,
    }


def main() -> None:
    df = pd.read_csv(TRAIN)
    print(f"train: {len(df)} rows, {df.pert.nunique()} perts, {df.gene.nunique()} genes\n")
    rows = [_seed_row(df, s) for s in range(5)]

    print("seed | cov | DE-AUROC | DIR-AUROC | gate(auroc,corr) | inc_mean | fused_mean")
    for r in rows:
        print(
            f"  {r['seed']}  | {r['cov']:.0%} |  {r['de_auroc']:.3f}  |   {r['dir_auroc']:.3f}   "
            f"| {str(r['gate']):>5}({r['gate_auroc']:.3f},{r['gate_corr']:.3f}) "
            f"| {r['inc_mean']:.3f}  |  {r['fused_mean']:.3f}"
        )

    def _m(k: str) -> tuple[float, float]:
        v = np.array([r[k] for r in rows], dtype=float)
        return float(np.nanmean(v)), float(np.nanstd(v))

    for k, note in [
        ("de_auroc", "chance ~0.50"),
        ("dir_auroc", "current DIR lever ~0.647"),
        ("cov", "family coverage"),
        ("inc_mean", "char two-stage alone"),
        ("fused_mean", f"vs LB {LB_MARK}"),
    ]:
        m, s = _m(k)
        print(f"{k:>10} mean={m:.3f} ± {s:.3f}  ({note})")
    n_pass = sum(r["gate"] for r in rows)
    print(f"\nCFA gate passed {n_pass}/5 seeds (min_auroc=0.55, max_abs_corr=0.5).")


if __name__ == "__main__":
    main()
