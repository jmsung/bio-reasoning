"""CollecTRI signed TF-regulon DE + direction feature (Goal 2).

Identity-free: the featurizer is built only from a curated edge set (TF → target
with an activating/repressing sign), so it applies unchanged to perts and genes
never seen in train. Under CRISPRi the perturbation gene is *knocked down*, so an
**activating** edge (TF normally drives the target) predicts the target goes
**down**, and a **repressing** edge predicts **up** — i.e. ``direction = -sign``.
"""

import numpy as np
import pandas as pd
import pytest

from bio_reasoning.features.tf_regulon import TFRegulonFeaturizer, coverage_report

# Stub CollecTRI-shaped edges: Tf1 activates GeneA, represses GeneB; Tf2 activates GeneC.
STUB_EDGES = pd.DataFrame(
    {
        "source": ["Tf1", "Tf1", "Tf2"],
        "target": ["GeneA", "GeneB", "GeneC"],
        "weight": [1.0, -1.0, 1.0],
    }
)


@pytest.fixture
def feat() -> TFRegulonFeaturizer:
    return TFRegulonFeaturizer(STUB_EDGES)


def test_de_indicator_edge_present_vs_absent(feat):
    de = feat.de_scores(["Tf1", "Tf1", "Tf2", "Tf1"], ["GeneA", "GeneB", "GeneC", "GeneC"])
    # first three are edges; Tf1→GeneC is not an edge
    assert de.tolist() == [1.0, 1.0, 1.0, 0.0]


def test_de_indicator_unknown_symbols_are_zero(feat):
    de = feat.de_scores(["Unseen", "Tf2"], ["GeneA", "Nope"])
    assert de.tolist() == [0.0, 0.0]


def test_direction_activating_is_down_repressing_is_up(feat):
    # activating edge (Tf1→GeneA, +1) under knockdown → target DOWN → -1
    # repressing edge (Tf1→GeneB, -1) under knockdown → target UP   → +1
    d = feat.direction_scores(["Tf1", "Tf1", "Tf2"], ["GeneA", "GeneB", "GeneC"])
    assert d.tolist() == [-1.0, 1.0, -1.0]


def test_direction_no_edge_is_zero(feat):
    d = feat.direction_scores(["Tf1", "Unseen"], ["GeneC", "GeneA"])
    assert d.tolist() == [0.0, 0.0]


def test_is_tf_covers_only_sources(feat):
    assert feat.is_tf("Tf1") and feat.is_tf("Tf2")
    assert not feat.is_tf("GeneA")  # a target, not a regulator
    assert not feat.is_tf("Unseen")


def test_coverage_report_counts(feat):
    perts = ["Tf1", "Tf1", "Tf2", "NotTf"]
    genes = ["GeneA", "GeneZ", "GeneC", "GeneA"]
    rep = coverage_report(feat, perts, genes)
    assert rep["n"] == 4
    # 3 of 4 perts are TFs
    assert rep["tf_covered_frac"] == pytest.approx(0.75)
    # 2 of 4 rows are actual regulon edges (Tf1→GeneA, Tf2→GeneC)
    assert rep["edge_frac"] == pytest.approx(0.5)
    # among the 3 TF-pert rows, 2 are edges
    assert rep["edge_among_tf_frac"] == pytest.approx(2 / 3)


def test_length_mismatch_raises(feat):
    with pytest.raises(ValueError):
        feat.de_scores(["Tf1", "Tf2"], ["GeneA"])


def test_weight_zero_treated_as_activating():
    edges = pd.DataFrame({"source": ["Tf1"], "target": ["GeneA"], "weight": [0.0]})
    f = TFRegulonFeaturizer(edges)
    # sign 0 → activating convention → knockdown drives target down
    assert f.direction_scores(["Tf1"], ["GeneA"]).tolist() == [-1.0]


def test_arrays_are_float_and_aligned(feat):
    de = feat.de_scores(np.array(["Tf1", "Tf2"]), np.array(["GeneA", "GeneC"]))
    assert de.dtype == float and de.shape == (2,)
