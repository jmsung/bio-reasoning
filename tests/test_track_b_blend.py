"""Tests for the Track B direction blend.

``blend_direction`` rank-averages the two-stage model's direction into a
submission while preserving the submission's DE magnitude (up+down). The
two-stage DE axis is deliberately unused — on the OOD split it is near-chance;
only its direction ranking is complementary. Tests pin DE preservation and the
w=0 / w=1 endpoints (direction order matches the base / the two-stage model).
"""

import numpy as np

from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.models.track_b_blend import blend_direction


def test_de_magnitude_preserved():
    up = np.array([0.2, 0.4, 0.1, 0.3])
    down = np.array([0.3, 0.1, 0.2, 0.3])
    ts_up = np.array([0.5, 0.1, 0.4, 0.2])
    ts_down = np.array([0.1, 0.5, 0.2, 0.4])
    nu, nd = blend_direction(up, down, ts_up, ts_down, weight=0.5)
    assert np.allclose(nu + nd, up + down)  # DE score untouched
    assert np.all(nu >= 0) and np.all(nd >= 0)


def test_weight_zero_keeps_base_direction_ranking():
    labels = np.array(["up", "down", "none", "up", "down", "none", "up", "none"])
    rng = np.random.default_rng(0)
    up, down = rng.random(8), rng.random(8)
    ts_up, ts_down = rng.random(8), rng.random(8)
    nu, nd = blend_direction(up, down, ts_up, ts_down, weight=0.0)
    # A monotonic (rank) transform of the direction leaves DIR AUROC unchanged.
    assert np.isclose(
        evaluate(labels, nu, nd)["auroc_dir"], evaluate(labels, up, down)["auroc_dir"]
    )


def test_weight_one_matches_two_stage_direction_ranking():
    labels = np.array(["up", "down", "none", "up", "down", "none", "up", "none"])
    rng = np.random.default_rng(1)
    up, down = rng.random(8), rng.random(8)
    ts_up, ts_down = rng.random(8), rng.random(8)
    nu, nd = blend_direction(up, down, ts_up, ts_down, weight=1.0)
    assert np.isclose(
        evaluate(labels, nu, nd)["auroc_dir"], evaluate(labels, ts_up, ts_down)["auroc_dir"]
    )
