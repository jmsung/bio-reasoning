"""Unit tests for the error-structure decomposition helpers."""

from __future__ import annotations

import numpy as np

from bio_reasoning.eval.error_structure import (
    axis_gap_budget,
    axis_scores,
    confident_wrong,
    coverage_dir_effect,
    per_group_axis,
)


def _perfect_case():
    """Labels with a pipeline that ranks both axes perfectly."""
    labels = np.array(["up", "down", "none", "up", "down", "none"])
    # up-rows: high up; down-rows: high down; none-rows: low both → perfect DE + DIR.
    up = np.array([0.9, 0.1, 0.05, 0.8, 0.2, 0.02])
    down = np.array([0.1, 0.9, 0.05, 0.2, 0.8, 0.02])
    return labels, up, down


def test_axis_scores_perfect():
    labels, up, down = _perfect_case()
    s = axis_scores(labels, up, down)
    assert s["auroc_de"] == 1.0
    assert s["auroc_dir"] == 1.0
    assert s["mean"] == 1.0
    assert s["n"] == 6
    assert s["n_de"] == 4


def test_axis_scores_single_class_group_is_nan():
    # All DE rows are "up" → DIR axis can't be ranked.
    labels = np.array(["up", "up", "none"])
    s = axis_scores(labels, np.array([0.9, 0.8, 0.1]), np.array([0.1, 0.2, 0.1]))
    assert np.isnan(s["auroc_dir"])
    assert s["auroc_de"] == 1.0


def test_axis_gap_budget_shares_sum_sensibly():
    labels, up, down = _perfect_case()
    b = axis_gap_budget(labels, up, down)
    assert b["de_gap"] == 0.0 and b["dir_gap"] == 0.0
    # Degenerate (no gap) → share is nan, not a crash.
    assert np.isnan(b["de_share"])

    # A pipeline strong on DE, weak on DIR → most remaining gap is on DIR.
    labels = np.array(["up", "down", "none", "up", "down", "none"])
    up = np.array([0.9, 0.85, 0.05, 0.8, 0.82, 0.02])  # DE separable, DIR ~random
    down = np.array([0.1, 0.15, 0.05, 0.2, 0.18, 0.02])
    b = axis_gap_budget(labels, up, down)
    assert b["de_share"] < 0.5  # DIR holds the larger share of remaining gap


def test_per_group_axis_drops_small_groups():
    labels = np.array(["up", "down", "none"] * 20)
    up = np.tile([0.9, 0.1, 0.05], 20)
    down = np.tile([0.1, 0.9, 0.05], 20)
    group = np.array(["big"] * 45 + ["tiny"] * 15)
    out = per_group_axis(labels, up, down, group, min_n=30)
    assert list(out["group"]) == ["big"]  # tiny (<30) dropped


def test_coverage_dir_effect_splits():
    labels = np.array(["up", "down", "up", "down"])
    up = np.array([0.9, 0.1, 0.5, 0.5])
    down = np.array([0.1, 0.9, 0.5, 0.5])
    covered = np.array([True, True, False, False])
    out = coverage_dir_effect(labels, up, down, covered)
    cov = out[out.subset == "covered"].iloc[0]
    assert cov["auroc_dir"] == 1.0  # covered rows ranked perfectly


def test_confident_wrong_flags():
    labels = np.array(["up", "down", "up", "none"])
    up = np.array([0.9, 0.9, 0.5, 0.0])  # row0 confident-right, row1 confident-WRONG, row2 unsure
    down = np.array([0.1, 0.1, 0.5, 0.0])
    out = confident_wrong(labels, up, down, dir_hi=0.75, dir_lo=0.25)
    assert len(out) == 3  # none row excluded
    assert bool(out.iloc[0]["confident"]) and not bool(out.iloc[0]["wrong"])
    assert bool(out.iloc[1]["confident"]) and bool(out.iloc[1]["wrong"])
    assert not bool(out.iloc[2]["confident"])
