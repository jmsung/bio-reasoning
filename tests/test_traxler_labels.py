"""Tests for Traxler log2FC → challenge-schema label thresholding."""

from __future__ import annotations

from bio_reasoning.data.traxler_labels import label_distribution, logfc_to_labels


def _lookup() -> dict[str, dict[str, float]]:
    return {
        "PertA": {"g_up": 1.5, "g_down": -2.0, "g_none": 0.3, "g_zero": 0.0},
        "PertB": {"g_up": 1.0, "g_down": -1.0, "g_bound": 0.99},  # boundary at |1.0|
    }


def test_thresholding_maps_to_up_down_none():
    df = logfc_to_labels(_lookup(), threshold=1.0)
    got = {(r.pert, r.gene): r.label for r in df.itertuples()}
    assert got[("PertA", "g_up")] == "up"
    assert got[("PertA", "g_down")] == "down"
    assert got[("PertA", "g_none")] == "none"  # |0.3| < 1.0
    assert got[("PertA", "g_zero")] == "none"
    assert got[("PertB", "g_up")] == "up"  # exactly at threshold counts as DE
    assert got[("PertB", "g_down")] == "down"
    assert got[("PertB", "g_bound")] == "none"  # 0.99 < 1.0


def test_schema_and_columns():
    df = logfc_to_labels(_lookup(), threshold=1.0)
    assert list(df.columns) == ["pert", "gene", "label", "log2fc"]
    assert set(df["label"].unique()) <= {"up", "down", "none"}
    assert len(df) == 7  # 4 + 3 pairs


def test_threshold_is_applied_and_not_all_none():
    strict = logfc_to_labels(_lookup(), threshold=2.5)  # only |2.0|<2.5 → all none here
    assert (strict["label"] == "none").all()
    loose = logfc_to_labels(_lookup(), threshold=0.5)
    assert (loose["label"] != "none").any()  # sanity: a real fold must have DE labels


def test_label_distribution_counts():
    df = logfc_to_labels(_lookup(), threshold=1.0)
    dist = label_distribution(df)
    assert dist["up"] == 2 and dist["down"] == 2 and dist["none"] == 3
    assert dist["n_perts"] == 2
