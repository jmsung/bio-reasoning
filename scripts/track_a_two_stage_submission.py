"""Build a Track A Kaggle submission from the two-stage GO-term model.

No LLM: fits the learned P(DE) and P(up|DE) heads over GO:BP term features
(`features/go_terms.py`) on all of train, then emits graded prediction_up/down
for test. GO terms for unseen test perts/genes are fetched from mygene.info on
first run and cached. Deterministic, so all three seed columns carry the same
value. Beats the evidence prior on the leak-free CV (~0.56 vs ~0.534).

Run: uv run --group eval python scripts/track_a_two_stage_submission.py
Then: kaggle competitions submit -c ml-gen-x-bioreasoning-challenge-track-a \
        -f submissions/track_a_two_stage.csv -m "<msg>"
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from bio_reasoning.eval.submission import to_submission_frame
from bio_reasoning.features.go_terms import GoPairFeaturizer
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
TEST = ROOT / "data/raw/track_a/test.csv"
PERT_CACHE = ROOT / "data/interim/pert_go_category.json"
GENE_CACHE = ROOT / "data/interim/gene_go_bp.json"
SAMPLE = ROOT / "configs/sample_submissions/track_a_sample_submission.csv"
OUT = ROOT / "submissions/track_a_two_stage.csv"
MODEL_NAME = "track-a-two-stage-go"


def build_submission(train: pd.DataFrame, test: pd.DataFrame, featurizer) -> pd.DataFrame:
    """Fit the two-stage GO model on train, return a schema-valid submission frame."""
    model = TwoStageDEDIR(featurizer=featurizer).fit(
        train.pert.tolist(), train.gene.tolist(), train.label.to_numpy()
    )
    up, down = model.predict(test.pert.tolist(), test.gene.tolist())

    traces = [
        f"two-stage GO: P(DE)={u + d:.3f} P(up|DE)={(u / (u + d) if (u + d) else 0.5):.3f}"
        for u, d in zip(up, down, strict=True)
    ]
    expected = pd.read_csv(SAMPLE, nrows=0).columns.tolist()
    out = to_submission_frame(test.id, up, down, MODEL_NAME, expected, traces=traces)
    assert len(out) == len(test), "row count mismatch vs test.csv"
    return out


def main() -> None:
    train = pd.read_csv(TRAIN)
    test = pd.read_csv(TEST)
    featurizer = GoPairFeaturizer(PERT_CACHE, GENE_CACHE)
    out = build_submission(train, test, featurizer)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT}  ({len(out)} rows)")
    de = out.prediction_up + out.prediction_down
    print(
        f"mean P(DE) on test: {de.mean():.3f}  mean P(up|DE): {(out.prediction_up / de).mean():.3f}"
    )


if __name__ == "__main__":
    main()
