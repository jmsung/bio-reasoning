import numpy as np
import pandas as pd
import pytest

from bio_reasoning.eval import kaggle_metric_track_a as mta
from bio_reasoning.eval import kaggle_metric_track_b as mtb

ID = "id"


def _solution(labels):
    return pd.DataFrame({ID: range(len(labels)), "label": labels})


def _submission(module, labels, up, down):
    """A schema-valid submission carrying every required column plus predictions."""
    df = pd.DataFrame({ID: range(len(labels)), "prediction_up": up, "prediction_down": down})
    for col in module.REQUIRED_COLUMNS:
        df[col] = 0  # numeric limit-checked cols default to 0; trace/name cols unused
    return df


# ---- Track A ----


def test_track_a_perfect_scores_one(de_labels):
    up = np.where(de_labels == "up", 1.0, 0.0)
    down = np.where(de_labels == "down", 1.0, 0.0)
    s = mta.score(_solution(de_labels), _submission(mta, de_labels, up, down), ID)
    assert s == 1.0


def test_track_a_constant_scores_half(de_labels):
    c = np.full(len(de_labels), 0.5)
    s = mta.score(_solution(de_labels), _submission(mta, de_labels, c, c), ID)
    assert abs(s - 0.5) < 1e-9


def test_track_a_matches_formula(de_labels):
    from sklearn.metrics import roc_auc_score

    rng = np.random.default_rng(0)
    up = rng.random(len(de_labels))
    down = rng.random(len(de_labels))
    exp_de = roc_auc_score((de_labels != "none").astype(int), up + down)
    m = de_labels != "none"
    exp_dir = roc_auc_score((de_labels[m] == "up").astype(int), up[m] / (up[m] + down[m]))
    s = mta.score(_solution(de_labels), _submission(mta, de_labels, up, down), ID)
    assert abs(s - (exp_de + exp_dir) / 2) < 1e-9


def test_track_a_missing_column_raises(de_labels):
    up = np.full(len(de_labels), 0.5)
    sub = _submission(mta, de_labels, up, up).drop(columns=["prompt_tokens"])
    with pytest.raises(mta.ParticipantVisibleError, match="prompt_tokens"):
        mta.score(_solution(de_labels), sub, ID)


def test_track_a_prompt_token_limit_raises(de_labels):
    up = np.full(len(de_labels), 0.5)
    sub = _submission(mta, de_labels, up, up)
    sub["prompt_tokens"] = mta.MAX_PROMPT_TOKENS + 1
    with pytest.raises(mta.ParticipantVisibleError, match="Prompt-token limit"):
        mta.score(_solution(de_labels), sub, ID)


# ---- Track B ----


def test_track_b_perfect_scores_one(de_labels):
    up = np.where(de_labels == "up", 1.0, 0.0)
    down = np.where(de_labels == "down", 1.0, 0.0)
    s = mtb.score(_solution(de_labels), _submission(mtb, de_labels, up, down), ID)
    assert s == 1.0


def test_track_b_constant_scores_half(de_labels):
    c = np.full(len(de_labels), 0.5)
    s = mtb.score(_solution(de_labels), _submission(mtb, de_labels, c, c), ID)
    assert abs(s - 0.5) < 1e-9


def test_track_b_tool_call_limit_raises(de_labels):
    up = np.full(len(de_labels), 0.5)
    sub = _submission(mtb, de_labels, up, up)
    sub["num_tool_calls"] = mtb.MAX_TOOL_CALLS_PER_ROW + 1
    with pytest.raises(mtb.ParticipantVisibleError, match="Tool-call limit"):
        mtb.score(_solution(de_labels), sub, ID)
