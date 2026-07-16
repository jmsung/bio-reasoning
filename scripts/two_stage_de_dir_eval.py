"""Evaluate the two-stage DE×DIR model on the dual-OOD split.

Tests which features let learned P(DE) and P(up|DE) heads beat the hand-set
evidence prior on the leak-free split where every pert and gene is unseen:

- **char-ngram** (`pair_features.py`): symbol strings only — at chance (~0.53),
  since gene/pert symbols are arbitrary.
- **GO-term** (`go_terms.py`): GO:BP term vocabularies for the pert *and* the
  target gene (the axis the prior ignores) — ~0.56, beating the prior.

Reports ``mean(AUROC_de, AUROC_dir)`` on the holdout val partition and under
5-fold doubly-disjoint CV, against the prior (~0.534) and no-signal 0.5.

Run: uv run --group eval python scripts/two_stage_de_dir_eval.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from bio_reasoning.eval.split import assert_leak_free, doubly_disjoint_folds, holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.features.gene_function import annotate_perts
from bio_reasoning.features.go_terms import GoPairFeaturizer
from bio_reasoning.features.pair_features import CharNgramFeaturizer
from bio_reasoning.models import track_a_prior
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
PERT_CACHE = ROOT / "data/interim/pert_go_category.json"
GENE_CACHE = ROOT / "data/interim/gene_go_bp.json"
K = 5
SEED = 0
PRIOR_FLOOR = 0.533


def _featurizers() -> dict[str, callable]:
    return {
        "char-ngram": CharNgramFeaturizer,
        "GO-term": lambda: GoPairFeaturizer(PERT_CACHE, GENE_CACHE),
    }


def _holdout(df: pd.DataFrame, labels: np.ndarray, make_feat) -> dict[str, float]:
    tr, val = holdout_split(df, seed=SEED)
    assert_leak_free(df, tr, val)
    model = TwoStageDEDIR(featurizer=make_feat()).fit(
        df.pert.iloc[tr], df.gene.iloc[tr], labels[tr]
    )
    up, down = model.predict(df.pert.iloc[val], df.gene.iloc[val])
    return evaluate(labels[val], up, down)


def _cv(df: pd.DataFrame, labels: np.ndarray, make_feat) -> tuple[float, float]:
    means = []
    for tr, ev in doubly_disjoint_folds(df, k=K, seed=SEED):
        assert_leak_free(df, tr, ev)
        model = TwoStageDEDIR(featurizer=make_feat()).fit(
            df.pert.iloc[tr], df.gene.iloc[tr], labels[tr]
        )
        up, down = model.predict(df.pert.iloc[ev], df.gene.iloc[ev])
        means.append(evaluate(labels[ev], up, down)["mean"])
    return float(np.nanmean(means)), float(np.nanstd(means))


def main() -> None:
    df = pd.read_csv(TRAIN)
    labels = df.label.to_numpy()
    print(f"train: {len(df)} rows, {df.pert.nunique()} perts, {df.gene.nunique()} genes")

    cats = annotate_perts(df.pert.tolist(), PERT_CACHE)
    up_prior, dn_prior = track_a_prior.predict(df.pert.tolist(), cats)
    const = np.full(len(df), 0.5)
    tr, val = holdout_split(df, seed=SEED)

    print("\n== dual-OOD holdout val ==")
    print(f"{'model':<26}{'auroc_de':>10}{'auroc_dir':>11}{'mean':>8}")
    for name, up, down in [
        ("no-signal (0.5/0.5)", const[val], const[val]),
        ("evidence prior", up_prior[val], dn_prior[val]),
    ]:
        r = evaluate(labels[val], up, down)
        print(f"{name:<26}{r['auroc_de']:>10.3f}{r['auroc_dir']:>11.3f}{r['mean']:>8.3f}")
    for name, make in _featurizers().items():
        r = _holdout(df, labels, make)
        print(
            f"{'two-stage ' + name:<26}{r['auroc_de']:>10.3f}{r['auroc_dir']:>11.3f}{r['mean']:>8.3f}"
        )

    print("\n== 5-fold doubly-disjoint CV (mean ± std) ==")
    prior_cv = [
        evaluate(labels[ev], up_prior[ev], dn_prior[ev])["mean"]
        for _, ev in doubly_disjoint_folds(df, k=K, seed=SEED)
    ]
    print(f"{'evidence prior':<26}{np.nanmean(prior_cv):>8.3f} ± {np.nanstd(prior_cv):.3f}")
    go_mean = 0.0
    for name, make in _featurizers().items():
        mu, sd = _cv(df, labels, make)
        print(f"{'two-stage ' + name:<26}{mu:>8.3f} ± {sd:.3f}")
        if name == "GO-term":
            go_mean = mu

    verdict = "beats" if go_mean > PRIOR_FLOOR else "does NOT beat"
    print(
        f"\nVerdict: the GO-term two-stage model {verdict} the prior floor "
        f"({go_mean:.3f} vs {PRIOR_FLOOR}). Char-ngrams over arbitrary symbols are at "
        "chance; GO:BP terms for the pert AND the target gene carry OOD-transferable signal."
    )


if __name__ == "__main__":
    main()
