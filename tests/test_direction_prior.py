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


def test_prior_scores_numeric_fallback(cache):
    # Used as the informed fallback when the agent fails to submit.
    up, down = direction_prior.prior_scores("Rpl13", cache)
    assert (round(up, 3), round(down, 3)) == (0.455, 0.195)  # housekeeping
    up2, down2 = direction_prior.prior_scores("Stat1", cache)
    assert (round(up2, 3), round(down2, 3)) == (0.220, 0.330)  # immune


def test_floor_to_prior_replaces_zero_tie(cache):
    # A (0,0) prediction is a zero-signal rank-metric tie -> replace with the prior.
    up, down = direction_prior.floor_to_prior(0.0, 0.0, "Rpl13", cache)
    assert (round(up, 3), round(down, 3)) == (0.455, 0.195)  # housekeeping prior


def test_floor_to_prior_leaves_nonzero_untouched(cache):
    # Any real signal is kept as-is — only the zero tie is floored.
    assert direction_prior.floor_to_prior(0.6, 0.15, "Rpl13", cache) == (0.6, 0.15)
    assert direction_prior.floor_to_prior(1.0, 0.0, "Rpl13", cache) == (1.0, 0.0)
    assert direction_prior.floor_to_prior(0.0, 1.0, "Rpl13", cache) == (0.0, 1.0)


def test_blend_endpoints(cache):
    # α=1 → agent passthrough; α=0 → pure prior.
    assert direction_prior.blend(0.6, 0.2, "Rpl13", 1.0, cache) == (0.6, 0.2)
    up, down = direction_prior.blend(0.6, 0.2, "Rpl13", 0.0, cache)
    assert (round(up, 3), round(down, 3)) == (0.455, 0.195)  # housekeeping prior


def test_blend_lifts_zero_tie(cache):
    # Any α<1 pulls a (0,0) tie off zero toward the prior.
    up, down = direction_prior.blend(0.0, 0.0, "Rpl13", 0.5, cache)
    # 0.5*0 + 0.5*(0.455, 0.195)
    assert (round(up, 4), round(down, 4)) == (0.2275, 0.0975)


def test_blend_is_convex_mix(cache):
    up, down = direction_prior.blend(0.8, 0.2, "Stat1", 0.5, cache)
    # 0.5*(0.8,0.2) + 0.5*prior(Stat1)=(0.22,0.33)
    assert (round(up, 3), round(down, 3)) == (0.510, 0.265)
    assert up + down <= 1.0 + 1e-9  # convex mix of two valid points stays valid


def test_public_tool_uses_default_cache():
    # The public tool wraps _prior_for with the shared cache path; just assert
    # the signature the DSPy ReAct loop calls exists and takes a single arg.
    assert direction_prior.direction_prior.__doc__
    assert "pert" in direction_prior.TOOL_SCHEMA["function"]["parameters"]["properties"]
