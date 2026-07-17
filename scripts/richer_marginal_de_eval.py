"""Goal 2: does adding DepMap essentiality to the marginal DE head clear the 0.55 gate?

The STRING-degree-only marginal head scored DE-AUROC 0.536 (first above-chance DE
channel, but below the 0.55 CFA bar). Essentiality is a second per-gene marginal:
essential/housekeeping genes are broadly responsive and transfer under dual-OOD
(housekeeping-transfer-hypothesis). This fits a logistic head on
``[log1p(pert_degree), log1p(gene_degree), pert_ess, gene_ess]`` over train and
measures standalone DE-AUROC on the dual-OOD val partition (seeds 0-4), reporting
both the degree-only baseline and the +essentiality candidate so the marginal lift
is explicit. Decisive: candidate ≥ 0.55 → a usable DE lever; still short → escalate
(continuous gene-effect / expression-atlas variance) or declare marginal DE capped.

Run: uv run --group eval python scripts/richer_marginal_de_eval.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.features.essentiality import load_essentiality
from bio_reasoning.features.marginal_properties import marginal_features
from bio_reasoning.features.string_graph import fetch_string_partners

_ROOT = Path(__file__).resolve().parents[1]
_DATA = (
    _ROOT / "data"
    if (_ROOT / "data/raw/track_a/train.csv").exists()
    else _ROOT.parent / "cb" / "data"
)
TRAIN = str(_DATA / "raw/track_a/train.csv")
PARTNERS_CACHE = str(_DATA / "external/string_partners_universe.json")
ESS_CACHE = str(_DATA / "external/depmap_essentiality.json")


def _auroc(df, degree, ess, seed):
    """Return (baseline_degree_only, candidate_with_essentiality) DE-AUROC for one seed."""
    tr, va = holdout_split(df, seed=seed, pert_frac=0.4, gene_frac=0.4)
    train, val = df.iloc[tr], df.iloc[va]
    de_tr = (train.label.to_numpy() != "none").astype(int)
    de_va = (val.label.to_numpy() != "none").astype(int)
    if len(set(de_tr)) < 2 or len(set(de_va)) < 2:
        return float("nan"), float("nan")

    def fit_score(essentiality):
        xtr = marginal_features(
            train.pert.tolist(), train.gene.tolist(), degree, log1p=True, essentiality=essentiality
        )
        xva = marginal_features(
            val.pert.tolist(), val.gene.tolist(), degree, log1p=True, essentiality=essentiality
        )
        head = LogisticRegression(max_iter=1000).fit(xtr, de_tr)
        return roc_auc_score(de_va, head.predict_proba(xva)[:, 1])

    return fit_score(None), fit_score(ess)


def main() -> None:
    df = pd.read_csv(TRAIN)
    partners = fetch_string_partners([], PARTNERS_CACHE)  # cache-hit → offline
    degree = {s: float(len(p)) for s, p in partners.items()}
    ternary = load_essentiality(ESS_CACHE)
    syms = sorted(set(df.pert.astype(str)) | set(df.gene.astype(str)))
    ess = {s: ternary[s.upper()] for s in syms if s.upper() in ternary}
    print(
        f"coverage: degree {np.mean([s in degree for s in syms]):.1%}, "
        f"essentiality {len(ess) / len(syms):.1%} of {len(syms)} symbols",
        flush=True,
    )

    base, cand = zip(*[_auroc(df, degree, ess, s) for s in range(5)], strict=True)
    for s, (b, c) in enumerate(zip(base, cand, strict=True)):
        print(f"seed {s}: degree-only {b:.3f} | +essentiality {c:.3f} | Δ {c - b:+.3f}", flush=True)
    bm, cm = float(np.nanmean(base)), float(np.nanmean(cand))
    print(
        f"\ndegree-only  DE-AUROC = {bm:.3f} ± {np.nanstd(base):.3f}\n"
        f"+essentiality DE-AUROC = {cm:.3f} ± {np.nanstd(cand):.3f}  (Δ {cm - bm:+.3f})\n"
        f"chance 0.50; CFA bar 0.55",
        flush=True,
    )
    print(
        "VERDICT:",
        (
            "CLEARS 0.55 — usable DE lever"
            if cm >= 0.55
            else "still short — escalate (continuous gene-effect / expr-atlas) or declare marginal DE capped"
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
