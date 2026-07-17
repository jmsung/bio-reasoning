"""Build + cache the aggregated PerturbQA external label store.

Reads the 8 curated PerturbQA CSVs (4 human CRISPRi lines x de/dir) and writes an
aggregated ``(PERT, GENE) -> {de_score, dir_score, n_de, n_dir}`` table to a cached
parquet, so the transfer-probe eval doesn't re-scan ~600k rows each run.

Leakage note: Track A is mouse macrophage CRISPRi; PerturbQA is human
K562/RPE1/HepG2/Jurkat — disjoint species AND cell type, so Track A cannot be
derived from it. Using it as external signal is sound.

Run: uv run --group eval python scripts/build_external_label_store.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from bio_reasoning.features.external_labels import load_perturbqa

ROOT = Path(__file__).resolve().parents[1]
PQ_DIR = ROOT / "data/external/perturbqa"
OUT = ROOT / "data/external/perturbqa_label_store.json"


def main() -> None:
    store = load_perturbqa(PQ_DIR)
    df = pd.DataFrame([{"pert": p, "gene": g, **v} for (p, g), v in store.items()])
    df.to_json(OUT, orient="records")
    de_pos = (df.de_score > 0).sum()
    print(f"cached {len(df):,} external (pert,gene) pairs -> {OUT.relative_to(ROOT)}")
    print(f"  DE-positive (any line): {de_pos:,}  | with direction: {(df.n_dir > 0).sum():,}")


if __name__ == "__main__":
    main()
