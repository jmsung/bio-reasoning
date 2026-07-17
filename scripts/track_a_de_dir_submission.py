"""Track A submission: two-stage GO model with the neighbour direction fused in.

Keeps the two-stage model's DE score (``prediction_up + prediction_down``) but
rank-fuses its direction ``P(up|DE)`` with the neighbour-retrieval channel's
direction (STRING-neighbour label borrowing, TRAIN-only) via
``fuse_neighbour_direction`` — the `feat/de-retrieval` finding that lifted OOD-val
mean +0.027 (Kaggle LB 0.585). STRING partners for train+test symbols are fetched
from string-db.org (mouse, taxid 10090) on first run and cached. Deterministic →
seed columns mirror the base.

Run: uv run --group eval python scripts/track_a_de_dir_submission.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from bio_reasoning.eval.submission import to_submission_frame
from bio_reasoning.features.go_terms import GoPairFeaturizer
from bio_reasoning.features.neighbor_retrieval import build_neighbor_graph, fuse_neighbour_direction
from bio_reasoning.features.string_graph import fetch_string_partners
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
TEST = ROOT / "data/raw/track_a/test.csv"
PERT_CACHE = ROOT / "data/interim/pert_go_category.json"
GENE_CACHE = ROOT / "data/interim/gene_go_bp.json"
STRING_CACHE = ROOT / "data/external/string_partners_submission.json"
SAMPLE = ROOT / "configs/sample_submissions/track_a_sample_submission.csv"
OUT = ROOT / "submissions/track_a_de_dir.csv"
MODEL_NAME = "track-a-two-stage-go+neighbour-dir"
# Neighbour-vs-model direction weight, tuned on OOD-val (feat/de-dir-weight-tuning):
# broad plateau w~0.7-0.8 (mean 0.588) vs equal-weight 0.584. 0.5 = the LB-0.585 baseline.
DIR_WEIGHT = 0.75


def build_submission(train: pd.DataFrame, test: pd.DataFrame, partners) -> pd.DataFrame:
    """Two-stage DE + neighbour-fused direction → schema-valid submission frame."""
    model = TwoStageDEDIR(featurizer=GoPairFeaturizer(PERT_CACHE, GENE_CACHE)).fit(
        train.pert.tolist(), train.gene.tolist(), train.label.to_numpy()
    )
    up, down = model.predict(test.pert.tolist(), test.gene.tolist())

    q = test[["pert", "gene"]].astype(str)
    pnb, gnb = build_neighbor_graph(q, partners, train)
    # min_support=3 tuned on OOD-val (feat/de-retrieval); don't lower without re-validating.
    fu, fd, covered = fuse_neighbour_direction(
        q, up, down, train, pnb, gnb, min_support=3, weight=DIR_WEIGHT
    )
    print(f"neighbour direction coverage on test: {covered.mean():.1%}", flush=True)
    traces = [
        f"two-stage GO DE + {'neighbour-fused' if c else 'model-only'} direction: "
        f"score_de={u + d:.3f} dir={(u / (u + d) if (u + d) else 0.5):.3f}"
        for u, d, c in zip(fu, fd, covered, strict=True)
    ]
    expected = pd.read_csv(SAMPLE, nrows=0).columns.tolist()
    out = to_submission_frame(test.id, fu, fd, MODEL_NAME, expected, traces=traces)
    assert len(out) == len(test), "row count mismatch vs test.csv"
    assert not out.isnull().any().any(), "submission has nulls"
    return out


def main() -> None:
    train = pd.read_csv(TRAIN)
    test = pd.read_csv(TEST)
    syms = sorted(
        set(train.pert.astype(str))
        | set(train.gene.astype(str))
        | set(test.pert.astype(str))
        | set(test.gene.astype(str))
    )
    partners = fetch_string_partners(syms, STRING_CACHE)
    out = build_submission(train, test, partners)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT}  ({len(out)} rows)", flush=True)


if __name__ == "__main__":
    main()
