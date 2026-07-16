"""Verify scripts/track_a_prompt_only.py builds a schema-valid Kaggle Track A submission.

Drives main() fully offline — post_chat_completion is stubbed to return empty, so every
row falls back to the uniform ternary prior (parse_answer("") = (1/3, 1/3)) with no
network — and asserts the emitted submission.csv + zip match the official 15-column
schema, cover every test id exactly once, contain no nulls, and stay under the 4,096
prompt-token cap.
"""

import importlib.util
import sys
import zipfile
from pathlib import Path

import pandas as pd

from bio_reasoning.eval.kaggle_metric_track_a import MAX_PROMPT_TOKENS, REQUIRED_COLUMNS

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "track_a_prompt_only.py"
_SAMPLE = _ROOT / "configs" / "sample_submissions" / "track_a_sample_submission.csv"

_TEST_ROWS = [
    ("Rpl3_g1", "Rpl3", "g1"),
    ("Il6_g2", "Il6", "g2"),
    ("Xyz_g3", "Xyz", "g3"),
]


def _load_script():
    spec = importlib.util.spec_from_file_location("track_a_prompt_only", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _empty_response(**_kwargs):
    return "", {"prompt_tokens": 0.0, "completion_tokens": 0.0, "total_tokens": 0.0}


def test_track_a_submission_is_schema_valid(tmp_path, monkeypatch):
    mod = _load_script()
    test_csv = tmp_path / "test.csv"
    pd.DataFrame(_TEST_ROWS, columns=["id", "pert", "gene"]).to_csv(test_csv, index=False)
    out_dir = tmp_path / "out"

    # Offline: every API call returns empty -> uniform-prior fallback, no network.
    monkeypatch.setattr(mod, "post_chat_completion", _empty_response)
    monkeypatch.setattr(
        sys,
        "argv",
        ["track_a_prompt_only.py", "--test-csv", str(test_csv), "--output-dir", str(out_dir)],
    )
    mod.main()

    sub = pd.read_csv(out_dir / "submission.csv")
    sample_cols = list(pd.read_csv(_SAMPLE).columns)

    # exact 15-column schema, order matches the sample submission
    assert list(sub.columns) == sample_cols
    for col in [*REQUIRED_COLUMNS, "prediction_up", "prediction_down"]:
        assert col in sub.columns, f"missing required column {col}"

    # full id coverage, one row per test id
    assert sorted(sub["id"]) == sorted(r[0] for r in _TEST_ROWS)
    assert sub["id"].is_unique

    # no nulls anywhere in the graded / metadata columns
    checked = [*REQUIRED_COLUMNS, "prediction_up", "prediction_down"]
    assert not sub[checked].isnull().any().any()

    # graded predictions are the uniform-prior fallback (empty responses)
    assert (abs(sub["prediction_up"] - 0.333) < 1e-6).all()

    # prompt-token cap respected
    assert sub["prompt_tokens"].max() <= MAX_PROMPT_TOKENS

    # zip packaged with the two required members
    with zipfile.ZipFile(out_dir / "submission_track_a.zip") as zf:
        assert set(zf.namelist()) == {"submission.csv", "prompt.txt"}
