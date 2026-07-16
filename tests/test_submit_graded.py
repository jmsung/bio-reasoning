"""Tests for the graded-submission path in the Track B agent harness.

Loads track_b_agentic by file path (scripts/ is not a package) with the scripts
dir on sys.path so its ``from tools.direction_prior import ...`` resolves.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS))
_spec = importlib.util.spec_from_file_location("track_b_agentic", _SCRIPTS / "track_b_agentic.py")
tba = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tba)


@pytest.mark.parametrize(
    "up,down,exp_up,exp_down",
    [
        (0.6, 0.15, 0.6, 0.15),  # in-range, kept as-is
        (-0.2, 0.5, 0.0, 0.5),  # negative clamped to 0
        (1.5, 0.0, 1.0, 0.0),  # >1 clamped to 1
        (0.8, 0.9, 0.8 / 1.7, 0.9 / 1.7),  # sum>1 renormalized
    ],
)
def test_clamp_pair(up, down, exp_up, exp_down):
    got_up, got_down = tba._clamp_pair(up, down)
    assert got_up == pytest.approx(exp_up)
    assert got_down == pytest.approx(exp_down)
    assert got_up + got_down <= 1.0 + 1e-9


def test_submit_graded_records_scores():
    out = tba.submit_graded(0.6, 0.15)
    assert "up=0.600" in out
    assert "down=0.150" in out
    assert "none=0.250" in out


def test_submit_graded_rejects_non_numeric():
    out = tba.submit_graded("abc", 0.1)
    assert out.startswith("Error")
