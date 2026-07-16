import numpy as np
import pandas as pd
import pytest

from bio_reasoning.eval import kaggle_metric_track_a as mta
from bio_reasoning.eval import kaggle_metric_track_b as mtb

ID = "id"
LABELS = ["up", "down", "none", "up", "down", "none", "up", "none"]


def _solution():
    return pd.DataFrame({ID: range(len(LABELS)), "label": LABELS})


def _submission(module, up, down):
    """A schema-valid submission carrying every required column plus predictions."""
    df = pd.DataFrame({ID: range(len(LABELS)), "prediction_up": up, "prediction_down": down})
    for col in module.REQUIRED_COLUMNS:
        df[col] = 0  # numeric limit-checked cols default to 0; trace/name cols unused
    return df


# ---- Track A ----


def test_track_a_perfect_scores_one():
    up = np.where(np.array(LABELS) == "up", 1.0, 0.0)
    down = np.where(np.array(LABELS) == "down", 1.0, 0.0)
    s = mta.score(_solution(), _submission(mta, up, down), ID)
    assert s == 1.0


def test_track_a_constant_scores_half():
    c = np.full(len(LABELS), 0.5)
    s = mta.score(_solution(), _submission(mta, c, c), ID)
    assert abs(s - 0.5) < 1e-9


def test_track_a_matches_formula():
    from sklearn.metrics import roc_auc_score

    rng = np.random.default_rng(0)
    up = rng.random(len(LABELS))
    down = rng.random(len(LABELS))
    labels = np.array(LABELS)
    exp_de = roc_auc_score((labels != "none").astype(int), up + down)
    m = labels != "none"
    exp_dir = roc_auc_score((labels[m] == "up").astype(int), up[m] / (up[m] + down[m]))
    s = mta.score(_solution(), _submission(mta, up, down), ID)
    assert abs(s - (exp_de + exp_dir) / 2) < 1e-9


def test_track_a_missing_column_raises():
    up = np.full(len(LABELS), 0.5)
    sub = _submission(mta, up, up).drop(columns=["prompt_tokens"])
    with pytest.raises(mta.ParticipantVisibleError, match="prompt_tokens"):
        mta.score(_solution(), sub, ID)


def test_track_a_prompt_token_limit_raises():
    up = np.full(len(LABELS), 0.5)
    sub = _submission(mta, up, up)
    sub["prompt_tokens"] = mta.MAX_PROMPT_TOKENS + 1
    with pytest.raises(mta.ParticipantVisibleError, match="Prompt-token limit"):
        mta.score(_solution(), sub, ID)


# ---- Track B ----


def test_track_b_perfect_scores_one():
    up = np.where(np.array(LABELS) == "up", 1.0, 0.0)
    down = np.where(np.array(LABELS) == "down", 1.0, 0.0)
    s = mtb.score(_solution(), _submission(mtb, up, down), ID)
    assert s == 1.0


def test_track_b_constant_scores_half():
    c = np.full(len(LABELS), 0.5)
    s = mtb.score(_solution(), _submission(mtb, c, c), ID)
    assert abs(s - 0.5) < 1e-9


def test_track_b_tool_call_limit_raises():
    up = np.full(len(LABELS), 0.5)
    sub = _submission(mtb, up, up)
    sub["num_tool_calls"] = mtb.MAX_TOOL_CALLS_PER_ROW + 1
    with pytest.raises(mtb.ParticipantVisibleError, match="Tool-call limit"):
        mtb.score(_solution(), sub, ID)
