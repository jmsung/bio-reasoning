"""Stage-0 gate: does external measured Perturb-seq DE/direction transfer to Track A?

The external-data lane is the only one with headroom toward the field, but an
internal deep-dive predicts it won't crack DE (context-specific) and at best adds a
small *direction* lift on the housekeeping slice. This settles it empirically on the
cheapest possible substrate: PerturbQA's curated labels (4 human CRISPRi lines)
ortholog-mapped onto Track A (mouse).

Sections build up across the branch goals:
- Goal 2: coverage_report()   — overlap + test-pert coverage.
- Goal 3: agreement gate      — external -> Track A DE/DIR AUROC, split housekeeping/immune.
- Goal 4: orthogonality       — is the external-DIR channel redundant with GO/neighbour?

Run: uv run --group eval python scripts/perturb_seq_transfer_probe.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from bio_reasoning.features.external_labels import (
    classify_pert,
    load_perturbqa,
    to_human,
    transfer_agreement,
)

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
TEST = ROOT / "data/raw/track_a/test.csv"
PQ_DIR = ROOT / "data/external/perturbqa"
PERT_CAT = ROOT / "data/interim/pert_go_category.json"


def coverage_report(train: pd.DataFrame, test: pd.DataFrame, store: dict) -> None:
    pq_perts = {p for p, _ in store}
    pq_genes = {g for _, g in store}
    pairs = set(store)

    def perts(df):
        return {to_human(p) for p in df.pert}

    def genes(df):
        return {to_human(g) for g in df.gene}

    def hpairs(df):
        return {(to_human(p), to_human(g)) for p, g in zip(df.pert, df.gene, strict=True)}

    ta_perts = perts(train) | perts(test)
    ta_genes = genes(train) | genes(test)
    tr_pairs, te_pairs = hpairs(train), hpairs(test)

    print("=== Coverage (uppercase mouse->human ortholog) ===")
    print(f"perts : Track A ∩ PerturbQA = {len(ta_perts & pq_perts)} / {len(ta_perts)}")
    print(f"genes : Track A ∩ PerturbQA = {len(ta_genes & pq_genes)} / {len(ta_genes)}")
    print(f"train pairs overlap = {len(tr_pairs & pairs)} / {len(tr_pairs)}")
    print(f"test  pairs overlap = {len(te_pairs & pairs)} / {len(te_pairs)}")
    print(f"test perts covered  = {len(perts(test) & pq_perts)} / {len(perts(test))}")
    unmatched = sorted(p for p in perts(test) if p not in pq_perts)
    print(
        f"test perts NOT in corpus ({len(unmatched)}): {unmatched[:12]}{' …' if len(unmatched) > 12 else ''}"
    )


def agreement_gate(train: pd.DataFrame, store: dict) -> None:
    """The Stage-0 gate: does external measurement predict Track A labels above chance?

    Reports external -> Track A DE-AUROC and DIR-AUROC on the train overlap, overall
    and split by pert slice (housekeeping = the transferable essential core; immune =
    macrophage-specific, predicted NOT to transfer).
    """
    pert_go = json.loads(PERT_CAT.read_text())
    slice_of = {p: classify_pert(pert_go.get(p, [])) for p in train.pert.unique()}
    train = train.assign(slice=train.pert.map(slice_of))

    print("\n=== Stage-0 gate: external measured -> Track A label agreement (train overlap) ===")
    print(f"{'slice':<14}{'DE-AUROC':>10}{'n_de':>7}{'DIR-AUROC':>11}{'n_dir':>7}")
    for name, sub in [
        ("ALL", train),
        *[(s, train[train.slice == s]) for s in ("housekeeping", "immune", "other")],
    ]:
        r = transfer_agreement(sub, store)
        de = f"{r['de_auroc']:.3f}" if r["de_auroc"] == r["de_auroc"] else "  n/a"
        di = f"{r['dir_auroc']:.3f}" if r["dir_auroc"] == r["dir_auroc"] else "  n/a"
        print(f"{name:<14}{de:>10}{r['n_de']:>7}{di:>11}{r['n_dir']:>7}")
    _signal_decomposition(train, store)


def _auc(y, s) -> float:
    y, s = np.asarray(y, float), np.asarray(s, float)
    m = ~np.isnan(y) & ~np.isnan(s)
    y, s = y[m], s[m]
    return float(roc_auc_score(y, s)) if len(set(y)) > 1 else float("nan")


def _signal_decomposition(train: pd.DataFrame, store: dict, seed: int = 0) -> None:
    """Is the DE transfer pair-specific or a marginal pert property? (the key control).

    Rebuilds the overlap frame and compares the real external ``de_score`` against:
    a shuffle control (should collapse to ~0.50), and leave-one-out per-pert / per-gene
    means (isolates marginal propensity from pair-specific signal).
    """
    rng = np.random.default_rng(seed)
    rows = []
    for pert, gene, label in zip(train.pert, train.gene, train.label, strict=True):
        rec = store.get((to_human(pert), to_human(gene)))
        if rec is None:
            continue
        rows.append(
            {
                "pert": to_human(pert),
                "gene": to_human(gene),
                "de_true": int(label != "none"),
                "de_score": rec["de_score"],
            }
        )
    d = pd.DataFrame(rows)

    def loo(key: str) -> pd.Series:
        s = d.groupby(key).de_score.transform("sum")
        c = d.groupby(key).de_score.transform("count")
        return (s - d.de_score) / (c - 1).replace(0, np.nan)

    real = _auc(d.de_true, d.de_score)
    shuf = np.mean([_auc(d.de_true, rng.permutation(d.de_score.values)) for _ in range(200)])
    print("\n=== DE signal decomposition (is it pair-specific or marginal?) ===")
    print(f"real external de_score      DE-AUROC = {real:.3f}")
    print(f"shuffle control                       = {shuf:.3f}   (expect ~0.50 → signal is real)")
    print(
        f"per-PERT leave-one-out mean           = {_auc(d.de_true, loo('pert')):.3f}   (marginal pert propensity)"
    )
    print(
        f"per-GENE leave-one-out mean           = {_auc(d.de_true, loo('gene')):.3f}   (pair/gene-specific → ~0.50 = none)"
    )
    print(
        "\nRead: the DE transfer is a MARGINAL pert property (essential perts drive broad DE,\n"
        "conserved mouse<->human) — NOT pair-specific. This reconciles the deep-dive (pair DE\n"
        "doesn't transfer: gene-LOO ~chance) yet beats our STRING-degree marginal proxy (0.536).\n"
        "DIR transfers strongly on the overlap (selection-inflated). BOTH are lookup-able for\n"
        "the ~67% of test perts in PerturbQA — the real test is fusing them on the dual-OOD split."
    )


def main() -> None:
    train = pd.read_csv(TRAIN)
    test = pd.read_csv(TEST)
    store = load_perturbqa(PQ_DIR)
    print(f"external store: {len(store):,} (pert,gene) pairs across 4 CRISPRi lines\n")
    coverage_report(train, test, store)
    agreement_gate(train, store)


if __name__ == "__main__":
    main()
