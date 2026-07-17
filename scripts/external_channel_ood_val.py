"""Does the external PerturbQA channel lift OOD-val over GO + neighbour-DIR?

The Stage-0 gate (`perturb_seq_transfer_probe.py`) showed external measured DE is a
*marginal pert-propensity* that transfers (pert-LOO 0.68, beating our internal
STRING-degree proxy 0.536) and direction transfers strongly on the overlap. This is
the payoff test: fuse the external channel (`external_pert_channel`) into our current
best (GO two-stage DE + neighbour-DIR) and measure the fused mean on the **dual-OOD
holdout split** — where perts AND genes are unseen, exactly where our internal DE is
chance and external lookup could add the pert-propensity we otherwise lack.

Baseline fuse s_de bus is GO's (neighbour is DIR-only), so the external DE channel must
add over GO's chance-level OOD DE, not over the fusion. Reported per seed to respect the
thin overlap / small-CV caution.

Measured (seeds 0/1/2): baseline 0.5663/0.5920/0.5874 → +ext DE+DIR 0.5680/0.6143/0.5858
(mean Δ +0.0075). The +0.72 overlap DE signal COLLAPSES on OOD — ext DE-AUROC on covered
val rows is only 0.504/0.565/0.517 (~chance), and the mean lift is ENTIRELY one-seed noise
(seed1 +0.022; seeds 0/2 +0.002/-0.002). CFA passes 1/3 seeds. The overlap 0.72/0.95 were
selection-inflated (robustly-DE easy pairs). Verdict: no robust OOD lift; lane closed.

Run: uv run --group eval python scripts/external_channel_ood_val.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.features.external_labels import external_pert_channel, load_perturbqa
from bio_reasoning.features.go_terms import GoPairFeaturizer
from bio_reasoning.features.neighbor_retrieval import build_neighbor_graph, neighbor_channel
from bio_reasoning.features.string_graph import fetch_string_partners
from bio_reasoning.models.fuse import Channel, cfa_gate, fuse
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
PERT_CACHE = ROOT / "data/interim/pert_go_category.json"
GENE_CACHE = ROOT / "data/interim/gene_go_bp.json"
STRING_CACHE = ROOT / "data/external/string_partners_universe.json"
PQ_DIR = ROOT / "data/external/perturbqa"
SEEDS = (0, 1, 2)


def _de_r(up: np.ndarray, down: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    de = up + down
    return de, np.divide(up, de, out=np.full_like(de, 0.5), where=de > 0)


def _auroc_de(labels, s_de, mask) -> float:
    from sklearn.metrics import roc_auc_score

    y = (labels[mask] != "none").astype(int)
    return float(roc_auc_score(y, np.asarray(s_de)[mask])) if len(set(y)) > 1 else float("nan")


def run_seed(df: pd.DataFrame, store: dict, seed: int) -> dict:
    tr, va = holdout_split(df, seed=seed)
    train, val = df.iloc[tr], df.iloc[va].reset_index(drop=True)
    labels = val.label.to_numpy()
    de_true = (labels != "none").astype(int)

    go = TwoStageDEDIR(featurizer=GoPairFeaturizer(PERT_CACHE, GENE_CACHE)).fit(
        train.pert, train.gene, train.label.to_numpy()
    )
    up_go, down_go = go.predict(val.pert.tolist(), val.gene.tolist())
    s_de_go, r_go = _de_r(up_go, down_go)

    syms = sorted(set(df.pert.astype(str)) | set(df.gene.astype(str)))
    partners = fetch_string_partners(syms, STRING_CACHE)
    q = val[["pert", "gene"]].astype(str)
    pnb, gnb = build_neighbor_graph(q, partners, train)
    nb = neighbor_channel(q, train, pnb, gnb, min_support=3)

    ext, covered = external_pert_channel(q, store)

    c_go = Channel("go", s_de=s_de_go, r=r_go)
    c_nb = Channel("nb", s_de=None, r=nb.r)
    c_ext = ext
    c_ext_de = Channel("ext-de", s_de=ext.s_de, r=None)
    c_ext_dir = Channel("ext-dir", s_de=None, r=ext.r)

    def mean_of(channels) -> float:
        u, d = fuse(channels)
        return evaluate(labels, u, d)["mean"]

    base = mean_of([c_go, c_nb])
    configs = {
        "baseline GO+nb": base,
        "+ext (DE+DIR)": mean_of([c_go, c_nb, c_ext]),
        "+ext (DE only)": mean_of([c_go, c_nb, c_ext_de]),
        "+ext (DIR only)": mean_of([c_go, c_nb, c_ext_dir]),
    }
    passed, stats = cfa_gate(ext.s_de, s_de_go, de_true)
    return {
        "seed": seed,
        "cov": int(covered.sum()),
        "n": len(val),
        "ext_de_auroc_cov": _auroc_de(labels, ext.s_de, covered),
        "go_de_auroc": float(evaluate(labels, up_go, down_go)["auroc_de"]),
        "cfa_pass": passed,
        "cfa_auroc": stats["auroc"],
        "cfa_corr": stats["corr"],
        "configs": configs,
    }


def main() -> None:
    df = pd.read_csv(TRAIN)
    store = load_perturbqa(PQ_DIR)
    results = [run_seed(df, store, s) for s in SEEDS]

    names = list(results[0]["configs"])
    print(
        f"\n{'config':<20}"
        + "".join(f"seed{r['seed']:>6}" for r in results)
        + f"{'mean':>9}{'Δ':>9}"
    )
    base_means = [r["configs"]["baseline GO+nb"] for r in results]
    for name in names:
        vals = [r["configs"][name] for r in results]
        mean = float(np.mean(vals))
        delta = mean - float(np.mean(base_means))
        print(f"{name:<20}" + "".join(f"{v:>10.4f}" for v in vals) + f"{mean:>9.4f}{delta:>+9.4f}")

    print("\nper-seed diagnostics:")
    for r in results:
        print(
            f"  seed {r['seed']}: ext covers {r['cov']}/{r['n']} val rows | "
            f"ext DE-AUROC(cov) {r['ext_de_auroc_cov']:.3f} vs GO DE-AUROC {r['go_de_auroc']:.3f} | "
            f"CFA {'PASS' if r['cfa_pass'] else 'REJECT'} "
            f"(auroc {r['cfa_auroc']:.3f}, |corr| {r['cfa_corr']:.3f})"
        )


if __name__ == "__main__":
    main()
