"""Offline tests for the survivor→submission bridge + the no-auto-submit invariant."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import bio_reasoning.trial_loop as tl
from bio_reasoning.trial_loop.submission import build_track_a_submission
from bio_reasoning.trial_loop.types import Variant

_EXPECTED_COLS = [
    "id",
    "prediction_up",
    "prediction_down",
    "prediction_up_seed42",
    "prediction_down_seed42",
    "reasoning_trace_seed42",
    "model_name",
]


def _test_df() -> pd.DataFrame:
    return pd.DataFrame(
        {"id": ["r0", "r1", "r2"], "pert": ["A", "B", "C"], "gene": ["x", "y", "z"]}
    )


def _fixed_predictor(rows, variant, seed, get_examples):
    # deterministic graded preds, independent of seed → averaging is a no-op
    table = {"A": (1.0, 0.0), "B": (0.0, 1.0), "C": (0.3, 0.3)}
    return [table[r["pert"]] for r in rows]


def test_build_submission_is_schema_valid_and_full_coverage():
    df = _test_df()
    sub = build_track_a_submission(
        df, Variant(id="cand", seeds=(42,)), _fixed_predictor, "jsagent-cand", _EXPECTED_COLS
    )
    assert list(sub.columns) == _EXPECTED_COLS
    assert len(sub) == 3 and sub["id"].tolist() == ["r0", "r1", "r2"]
    assert sub["prediction_up"].tolist() == [1.0, 0.0, 0.3]
    assert sub["model_name"].unique().tolist() == ["jsagent-cand"]


def test_build_submission_averages_over_variant_seeds():
    df = _test_df()
    seen = []

    def seed_varying(rows, variant, seed, get_examples):
        seen.append(seed)
        val = 1.0 if seed == 42 else 0.0  # up=1 at seed42, up=0 at seed43 → mean 0.5
        return [(val, 0.0) for _ in rows]

    sub = build_track_a_submission(
        df, Variant(id="c", seeds=(42, 43)), seed_varying, "m", _EXPECTED_COLS
    )
    assert seen == [42, 43]  # both self-consistency samples drawn
    assert sub["prediction_up"].tolist() == [0.5, 0.5, 0.5]


def test_loop_package_and_runner_never_auto_submit():
    # the human-gated invariant, machine-locked: no code path invokes Kaggle.
    pkg_dir = Path(tl.__file__).resolve().parent
    runner = pkg_dir.parents[2] / "scripts" / "self_improve_loop.py"
    sources = list(pkg_dir.glob("*.py")) + ([runner] if runner.exists() else [])
    assert runner.exists(), "runner script not found for the guard"
    # invariant = no code *executes* a submission; a documented manual command is fine.
    for src in sources:
        text = src.read_text()
        assert "import kaggle" not in text
        assert "kaggle.api" not in text
        assert "os.system" not in text
        assert "subprocess" not in text
