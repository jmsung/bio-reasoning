"""Goal 5 test: scripts/track_b_blend_two_stage_submission.py preserves schema + DE.

Drives blend_submission() offline against pre-seeded GO caches and asserts the
output keeps all Track B columns and metadata, preserves each row's DE magnitude
(up+down), and covers the same ids.
"""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

import bio_reasoning.features.gene_function as gf
from bio_reasoning.features.go_terms import GoPairFeaturizer

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "track_b_blend_two_stage_submission.py"


def _load():
    spec = importlib.util.spec_from_file_location("track_b_blend_two_stage_submission", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_blend_preserves_schema_and_de(tmp_path, monkeypatch, write_go_cache):
    mod = _load()
    monkeypatch.setattr(gf, "_fetch_go_bp", lambda s: (_ for _ in ()).throw(AssertionError(s)))

    train = pd.DataFrame(
        {
            "id": [f"P{i}_G{i}" for i in range(9)],
            "pert": [f"P{i}" for i in range(9)],
            "gene": [f"G{i}" for i in range(9)],
            "label": (["up", "down", "none"] * 3),
        }
    )
    test = pd.DataFrame({"id": ["Pa_Gz", "Pb_Gy"], "pert": ["Pa", "Pb"], "gene": ["Gz", "Gy"]})
    sub = pd.DataFrame(
        {
            "id": ["Pa_Gz", "Pb_Gy"],
            "prediction_up": [0.2, 0.4],
            "prediction_down": [0.3, 0.1],
            "reasoning_trace": ["{}", "{}"],
            "tokens_used": [10, 20],
            "num_tool_calls": [1, 2],
            "prompt_tokens": [5, 6],
            "num_distinct_tools": [1, 1],
            "model_name": ["m", "m"],
        }
    )
    pgo = {p: ["translation"] for p in [*train.pert, *test.pert]}
    ggo = {g: ["ribosome"] for g in [*train.gene, *test.gene]}
    feat = GoPairFeaturizer(write_go_cache(pgo, "p.json"), write_go_cache(ggo, "g.json"), min_df=1)

    out = mod.blend_submission(sub, test, train, feat, weight=0.5)

    assert list(out.columns) == list(sub.columns)  # all metadata kept
    assert list(out.id) == list(sub.id)
    # DE magnitude preserved per row; metadata untouched.
    assert np.allclose(
        out.prediction_up + out.prediction_down, sub.prediction_up + sub.prediction_down
    )
    assert list(out.reasoning_trace) == list(sub.reasoning_trace)
    assert list(out.model_name) == list(sub.model_name)
