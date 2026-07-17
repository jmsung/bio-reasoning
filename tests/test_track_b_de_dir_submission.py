"""Goal 2 test: Track B neighbour-direction fusion preserves schema, metadata, DE ranking."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "track_b_de_dir_submission.py"


def _load():
    spec = importlib.util.spec_from_file_location("track_b_de_dir_submission", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_neighbour_fuse_submission_keeps_schema_metadata_and_de_ranking():
    mod = _load()
    train = pd.DataFrame(
        {
            "pert": ["Pa", "Pa", "Pb", "Pc"],
            "gene": ["G1", "G2", "G1", "G3"],
            "label": ["up", "none", "up", "down"],
        }
    )
    test = pd.DataFrame({"id": ["Q_Gq", "Zz_Yy"], "pert": ["Q", "Zz"], "gene": ["Gq", "Yy"]})
    sub = pd.DataFrame(
        {
            "id": ["Q_Gq", "Zz_Yy"],
            "prediction_up": [0.30, 0.10],
            "prediction_down": [0.20, 0.30],  # base DE = [0.5, 0.4]
            "reasoning_trace": ["{}", "{}"],
            "tokens_used": [10, 20],
            "num_tool_calls": [1, 2],
            "prompt_tokens": [5, 6],
            "num_distinct_tools": [1, 1],
            "model_name": ["m", "m"],
        }
    )
    partners = {"Q": {"Pa", "Pb"}}  # Q's neighbours are train perts → covered; Zz not

    out = mod.neighbour_fuse_submission(sub, test, train, partners, min_support=1)

    assert list(out.columns) == list(sub.columns)  # schema + metadata kept
    assert list(out.id) == list(sub.id)
    assert list(out.reasoning_trace) == list(sub.reasoning_trace)
    assert list(out.model_name) == list(sub.model_name)
    # DE ranking preserved (fuse rank-normalizes the base DE monotonically)
    assert np.array_equal(
        rankdata(out.prediction_up + out.prediction_down),
        rankdata(sub.prediction_up + sub.prediction_down),
    )
    assert (out.prediction_up >= 0).all() and (out.prediction_down >= 0).all()
