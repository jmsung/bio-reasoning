"""Shared Track A submission-frame builder — schema-valid, seed columns mirror the base."""

import numpy as np
import pytest

from bio_reasoning.eval.submission import to_submission_frame

_COLS = [
    "id",
    "prediction_up",
    "prediction_down",
    "prediction_up_seed42",
    "prediction_down_seed42",
    "reasoning_trace_seed42",
    "prediction_up_seed43",
    "prediction_down_seed43",
    "reasoning_trace_seed43",
    "prediction_up_seed44",
    "prediction_down_seed44",
    "reasoning_trace_seed44",
    "tokens_used",
    "prompt_tokens",
    "model_name",
]


def test_frame_has_exact_schema_and_mirrors_seeds():
    ids = ["a", "b"]
    up = np.array([0.7, 0.2])
    down = np.array([0.1, 0.6])
    out = to_submission_frame(ids, up, down, "m", _COLS)
    assert list(out.columns) == _COLS
    assert len(out) == 2
    for s in (42, 43, 44):
        assert np.allclose(out[f"prediction_up_seed{s}"], up)
        assert np.allclose(out[f"prediction_down_seed{s}"], down)
    assert (out["model_name"] == "m").all()
    assert (out["prompt_tokens"] == 0).all()


def test_frame_raises_on_missing_expected_column():
    with pytest.raises((KeyError, AssertionError)):
        to_submission_frame(["a"], np.array([0.5]), np.array([0.5]), "m", _COLS + ["bogus"])


def test_frame_accepts_custom_traces():
    out = to_submission_frame(["a"], np.array([0.5]), np.array([0.5]), "m", _COLS, traces=["hi"])
    assert out["reasoning_trace_seed42"].iloc[0] == "hi"
