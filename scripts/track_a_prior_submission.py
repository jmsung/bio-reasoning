"""Build a Track A Kaggle submission from the evidence-grounded prior.

No LLM: emits graded prediction_up/down from the perturbation's functional
category (see models/track_a_prior). Deterministic, so all three seed columns
carry the same value. Establishes a real leaderboard number to calibrate our
leak-free local CV (~0.534) against the public LB.

Run: uv run --group eval python scripts/track_a_prior_submission.py
Then: kaggle competitions submit -c ml-gen-x-bioreasoning-challenge-track-a \
        -f submissions/track_a_prior_baseline.csv -m "<msg>"
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from bio_reasoning.features.gene_function import annotate_perts
from bio_reasoning.models import track_a_prior

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "data/raw/track_a/test.csv"
CACHE = ROOT / "data/interim/pert_go_category.json"
SAMPLE = ROOT / "configs/sample_submissions/track_a_sample_submission.csv"
OUT = ROOT / "submissions/track_a_prior_baseline.csv"
MODEL_NAME = "track-a-prior-baseline"


def main() -> None:
    test = pd.read_csv(TEST)
    cats = annotate_perts(test.pert.tolist(), CACHE)
    up, down = track_a_prior.predict(test.pert.tolist(), cats)

    traces = [
        f"prior: pert '{p}' -> category '{cats.get(p, 'other')}'; up={u:.3f} down={d:.3f}"
        for p, u, d in zip(test.pert, up, down, strict=True)
    ]
    out = pd.DataFrame({"id": test.id, "prediction_up": up, "prediction_down": down})
    for seed in (42, 43, 44):  # deterministic prior -> identical per seed
        out[f"prediction_up_seed{seed}"] = up
        out[f"prediction_down_seed{seed}"] = down
        out[f"reasoning_trace_seed{seed}"] = traces
    out["tokens_used"] = 0
    out["prompt_tokens"] = 0  # no LLM; well under the 4,096 cap
    out["model_name"] = MODEL_NAME

    expected = pd.read_csv(SAMPLE, nrows=0).columns.tolist()
    out = out[expected]  # exact column order; raises if any is missing
    assert list(out.columns) == expected, "column mismatch vs sample submission"
    assert len(out) == len(test), "row count mismatch vs test.csv"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT}  ({len(out)} rows)")
    print(
        f"category mix on test: {pd.Series([cats[p] for p in test.pert]).value_counts().to_dict()}"
    )


if __name__ == "__main__":
    main()
