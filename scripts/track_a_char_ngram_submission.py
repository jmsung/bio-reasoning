"""Real-test-difficulty probe: a char-ngram two-stage Track A submission.

The char-ngram (TF-IDF) two-stage model scores ~0.49-0.53 on our dual-OOD
`holdout_split` — near chance, because symbols are arbitrary on a split that holds
out *both* perts and genes. The public field reportedly reaches ~0.693 with the
same features. Submitting this to the real LB measures the gap: LB≈0.52 → our split
is honest; LB≈0.69 → the real test is easier than our split and DE is learnable
there (we've been sandbagging). This submission is the *measurement*, not a model.

Run: uv run --group eval python scripts/track_a_char_ngram_submission.py
Then: kaggle competitions submit -c ml-gen-x-bioreasoning-challenge-track-a \
        -f submissions/track_a_char_ngram.csv -m "<msg>"
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.eval.submission import to_submission_frame
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.features.pair_features import CharNgramFeaturizer
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/track_a/train.csv"
TEST = ROOT / "data/raw/track_a/test.csv"
SAMPLE = ROOT / "configs/sample_submissions/track_a_sample_submission.csv"
OUT = ROOT / "submissions/track_a_char_ngram.csv"
MODEL_NAME = "track-a-char-ngram-tfidf-probe"


def build_submission(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    """Fit the char-ngram two-stage model on all train, return a schema-valid frame."""
    model = TwoStageDEDIR(featurizer=CharNgramFeaturizer()).fit(
        train.pert.tolist(), train.gene.tolist(), train.label.to_numpy()
    )
    up, down = model.predict(test.pert.tolist(), test.gene.tolist())
    traces = [
        f"char-ngram two-stage: P(DE)={u + d:.3f} P(up|DE)={(u / (u + d) if (u + d) else 0.5):.3f}"
        for u, d in zip(up, down, strict=True)
    ]
    expected = pd.read_csv(SAMPLE, nrows=0).columns.tolist()
    out = to_submission_frame(test.id, up, down, MODEL_NAME, expected, traces=traces)
    assert len(out) == len(test), "row count mismatch vs test.csv"
    assert not out.isnull().any().any(), "submission has nulls"
    return out


def main() -> None:
    train = pd.read_csv(TRAIN)
    test = pd.read_csv(TEST)

    # Record the OOD-val score for the LB↔val gap (the whole point of the probe).
    tr, val = holdout_split(train, seed=0)
    m = TwoStageDEDIR(featurizer=CharNgramFeaturizer()).fit(
        train.pert.iloc[tr], train.gene.iloc[tr], train.label.to_numpy()[tr]
    )
    u, d = m.predict(train.pert.iloc[val], train.gene.iloc[val])
    r = evaluate(train.label.to_numpy()[val], u, d)
    print(
        f"char-ngram two-stage OOD-val (holdout seed 0): "
        f"de={r['auroc_de']:.3f} dir={r['auroc_dir']:.3f} mean={r['mean']:.3f}",
        flush=True,
    )

    out = build_submission(train, test)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    de = np.asarray(out.prediction_up + out.prediction_down, dtype=float)
    print(f"wrote {OUT}  ({len(out)} rows); mean P(DE) on test {de.mean():.3f}", flush=True)


if __name__ == "__main__":
    main()
