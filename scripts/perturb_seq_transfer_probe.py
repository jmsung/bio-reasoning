"""Stage-0 gate: does external measured Perturb-seq DE/direction transfer to Track A?

The external-data lane is the only one with headroom toward the field, but the
3-agent deep-dive (`mb/notes/perturb-seq-data-lane.md`) predicts it won't crack DE
(context-specific) and at best adds a small *direction* lift on the housekeeping
slice. This settles it empirically on the cheapest possible substrate: PerturbQA's
curated labels (4 human CRISPRi lines) ortholog-mapped onto Track A (mouse).

Sections build up across the branch goals:
- Goal 2: coverage_report()   — overlap + test-pert coverage.
- Goal 3: agreement gate      — external -> Track A DE/DIR AUROC, split housekeeping/immune.
- Goal 4: orthogonality       — is the external-DIR channel redundant with GO/neighbour?

Run: uv run --group eval python scripts/perturb_seq_transfer_probe.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from bio_reasoning.features.external_labels import load_perturbqa, to_human

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


def main() -> None:
    train = pd.read_csv(TRAIN)
    test = pd.read_csv(TEST)
    store = load_perturbqa(PQ_DIR)
    print(f"external store: {len(store):,} (pert,gene) pairs across 4 CRISPRi lines\n")
    coverage_report(train, test, store)


if __name__ == "__main__":
    main()
