"""Goal 2 test: scripts/track_a_de_dir_submission.py builds a valid submission.

Drives build_submission() fully offline — injected STRING partners, pre-seeded GO
caches, no network — and asserts the fused frame matches the official Track A
schema, covers every test id once, and has NO nulls (the empty-trace-as-NaN bug).
"""

import importlib.util
from pathlib import Path

import pandas as pd

import bio_reasoning.features.gene_function as gf
from bio_reasoning.eval.kaggle_metric_track_a import MAX_PROMPT_TOKENS

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "track_a_de_dir_submission.py"
_SAMPLE = _ROOT / "configs" / "sample_submissions" / "track_a_sample_submission.csv"


def _load():
    spec = importlib.util.spec_from_file_location("track_a_de_dir_submission", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_build_submission_is_schema_valid_and_null_free(monkeypatch, write_go_cache):
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

    pgo = {p: ["translation"] for p in [*train.pert, *test.pert]}
    ggo = {g: ["ribosome"] for g in [*train.gene, *test.gene]}
    monkeypatch.setattr(mod, "PERT_CACHE", write_go_cache(pgo, name="pert.json"))
    monkeypatch.setattr(mod, "GENE_CACHE", write_go_cache(ggo, name="gene.json"))

    # Pa neighbours P0/P1 (train perts) → the test row borrows their labels; leak-free.
    partners = {"Pa": {"P0", "P1", "P2"}, "Gz": {"G0"}}

    out = mod.build_submission(train, test, partners)

    sample_cols = list(pd.read_csv(_SAMPLE).columns)
    assert list(out.columns) == sample_cols
    assert set(out.id) == set(test.id)
    assert out.notna().all().all()  # the empty-trace null bug must stay fixed
    assert out.prompt_tokens.max() <= MAX_PROMPT_TOKENS
    assert (out.prediction_up >= 0).all() and (out.prediction_down >= 0).all()
