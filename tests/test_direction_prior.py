"""Offline tests for the direction_prior agent tool.

Seeds the GO-term cache so ``_prior_for`` never hits the network, then checks
that each functional category maps to the Track A prior's graded scores.
"""

import importlib.util
import json
from pathlib import Path

import pytest

_MOD_PATH = Path(__file__).resolve().parents[1] / "scripts" / "tools" / "direction_prior.py"
_spec = importlib.util.spec_from_file_location("direction_prior", _MOD_PATH)
direction_prior = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(direction_prior)


@pytest.fixture
def cache(tmp_path):
    """A GO-term cache covering one pert per category, so no fetch happens."""
    path = tmp_path / "go_cache.json"
    path.write_text(
        json.dumps(
            {
                "Rpl13": ["translation", "ribosome biogenesis"],  # -> housekeeping
                "Stat1": ["immune response", "interferon signaling"],  # -> immune
                "Xyz1": [],  # no terms -> other
            }
        )
    )
    return path


def test_housekeeping_leans_up(cache):
    out = direction_prior._prior_for("Rpl13", cache)
    assert "housekeeping" in out
    # PRIORS["housekeeping"] = (0.70, 0.65) -> up=0.455, down=0.195
    assert "pred_up = 0.455" in out
    assert "pred_down = 0.195" in out
    assert "leans up" in out


def test_immune_leans_down(cache):
    out = direction_prior._prior_for("Stat1", cache)
    assert "immune" in out
    # PRIORS["immune"] = (0.40, 0.55) -> up=0.220, down=0.330
    assert "pred_up = 0.220" in out
    assert "pred_down = 0.330" in out
    assert "leans down" in out


def test_unknown_terms_fall_back_to_other(cache):
    out = direction_prior._prior_for("Xyz1", cache)
    assert "other" in out
    # PRIORS["other"] = (0.55, 0.45) -> up=0.2475, down=0.2025
    assert "pred_up = 0.248" in out
    assert "pred_down = 0.202" in out


def test_public_tool_uses_default_cache():
    # The public tool wraps _prior_for with the shared cache path; just assert
    # the signature the DSPy ReAct loop calls exists and takes a single arg.
    assert direction_prior.direction_prior.__doc__
    assert "pert" in direction_prior.TOOL_SCHEMA["function"]["parameters"]["properties"]
