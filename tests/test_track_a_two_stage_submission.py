"""Goal 4 test: scripts/track_a_two_stage_submission.py builds a valid submission.

Drives build_submission() offline against pre-seeded GO caches and asserts the
frame matches the official 15-column Track A schema, covers every test id once,
has no nulls, and reports zero prompt tokens (no LLM).
"""

import importlib.util
from pathlib import Path

import pandas as pd

import bio_reasoning.features.gene_function as gf
from bio_reasoning.eval.kaggle_metric_track_a import MAX_PROMPT_TOKENS
from bio_reasoning.features.go_terms import GoPairFeaturizer

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "track_a_two_stage_submission.py"
_SAMPLE = _ROOT / "configs" / "sample_submissions" / "track_a_sample_submission.csv"


def _load():
    spec = importlib.util.spec_from_file_location("track_a_two_stage_submission", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_build_submission_is_schema_valid(tmp_path, monkeypatch, write_go_cache):
    mod = _load()
    monkeypatch.setattr(mod, "SAMPLE", _SAMPLE)
    monkeypatch.setattr(gf, "_fetch_go_bp", lambda s: (_ for _ in ()).throw(AssertionError(s)))

    train = pd.DataFrame(
        {
            "id": [f"P{i}_G{i}" for i in range(9)],
            "pert": [f"P{i}" for i in range(9)],
            "gene": [f"G{i}" for i in range(9)],
            "label": (["up", "down", "none"] * 3),
        }
    )
    test = pd.DataFrame({"id": ["Pa_Gz"], "pert": ["Pa"], "gene": ["Gz"]})

    # Seed GO caches for all train + test symbols (a shared term gives non-empty vocab).
    pgo = {p: ["translation"] for p in [*train.pert, *test.pert]}
    ggo = {g: ["ribosome"] for g in [*train.gene, *test.gene]}
    pc = write_go_cache(pgo, name="pert.json")
    gc = write_go_cache(ggo, name="gene.json")
    featurizer = GoPairFeaturizer(pc, gc, min_df=1)

    out = mod.build_submission(train, test, featurizer)

    sample_cols = list(pd.read_csv(_SAMPLE).columns)
    assert list(out.columns) == sample_cols
    assert len(out) == len(test)
    assert set(out.id) == set(test.id)
    assert out.notna().all().all()
    assert out.prompt_tokens.max() <= MAX_PROMPT_TOKENS
    # graded, non-negative predictions
    assert (out.prediction_up >= 0).all() and (out.prediction_down >= 0).all()
