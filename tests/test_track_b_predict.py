"""Offline tests for the Track B agent runner's prediction logic.

Covers ``extract_prediction`` (trace → graded up/down — the exact path whose 0/0
abstention collapsed LB to 0.488) and ``predict_row`` (agent call + extraction,
with a fake ReAct so no model/network is needed). Loads ``track_b_agentic`` by
file path, matching ``test_submit_graded``.
"""

import importlib.util
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS))
_spec = importlib.util.spec_from_file_location("track_b_agentic", _SCRIPTS / "track_b_agentic.py")
tba = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tba)

_PRIOR = (0.6, 0.1)


def _prior_fn(pert):
    return _PRIOR


def test_extract_prefers_submit_graded():
    trace = {
        "tool_name_0": "submit_graded",
        "tool_args_0": {"prediction_up": 0.7, "prediction_down": 0.2},
    }
    assert tba.extract_prediction(trace, "", "Pert", prior_fn=_prior_fn) == (0.7, 0.2)


def test_extract_graded_is_clamped():
    trace = {
        "tool_name_0": "submit_graded",
        "tool_args_0": {"prediction_up": 1.5, "prediction_down": -0.2},
    }
    assert tba.extract_prediction(trace, "", "Pert", prior_fn=_prior_fn) == (1.0, 0.0)


def test_extract_submit_answer_letter():
    trace = {"tool_name_0": "submit_answer", "tool_args_0": {"answer": "A"}}
    assert tba.extract_prediction(trace, "", "Pert", prior_fn=_prior_fn) == tba.parse_answer("A")


def test_extract_falls_back_to_prior_when_unparseable():
    # No usable tool call and empty final text → evidence prior, never 0/0 or 1/3.
    assert tba.extract_prediction({}, "", "Pert", prior_fn=_prior_fn) == _PRIOR


def test_extract_bad_graded_args_fall_through_to_prior():
    trace = {
        "tool_name_0": "submit_graded",
        "tool_args_0": {"prediction_up": "not-a-number", "prediction_down": 0.2},
    }
    assert tba.extract_prediction(trace, "", "Pert", prior_fn=_prior_fn) == _PRIOR


class _FakeResult:
    def __init__(self, answer, trajectory):
        self.answer = answer
        self.trajectory = trajectory


def test_predict_row_runs_agent_and_extracts():
    def fake_react(question):
        return _FakeResult(
            "",
            {
                "tool_name_0": "submit_graded",
                "tool_args_0": {"prediction_up": 0.8, "prediction_down": 0.1},
            },
        )

    assert tba.predict_row(fake_react, "Pert", "Gene", prior_fn=_prior_fn) == (0.8, 0.1)


def test_predict_row_agent_crash_falls_back_to_prior():
    def boom(question):
        raise RuntimeError("agent died")

    assert tba.predict_row(boom, "Pert", "Gene", prior_fn=_prior_fn) == _PRIOR
