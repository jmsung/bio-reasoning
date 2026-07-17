"""Goal 1: marginal (per-symbol) DE features — pert breadth × gene responsiveness.

Unlike the five failed pair-interaction channels, these features are per-pert and
per-gene *marginal* connectivity (STRING degree), which transfer to unseen val
symbols under the dual-OOD split. Missing symbols get degree 0 (uncovered).
"""

import numpy as np

from bio_reasoning.features.marginal_properties import marginal_features


def _degrees():
    return {"Pa": 100, "Pb": 5, "G1": 50, "G2": 3}


def test_features_lookup_pert_and_gene_degree():
    X = marginal_features(["Pa", "Pb"], ["G1", "G2"], _degrees())
    assert X.shape == (2, 2)  # [pert_degree, gene_degree] per row
    assert X[0, 0] == 100 and X[0, 1] == 50
    assert X[1, 0] == 5 and X[1, 1] == 3


def test_missing_symbol_is_zero_degree():
    X = marginal_features(["Zz"], ["Gy"], _degrees())
    assert X[0, 0] == 0 and X[0, 1] == 0


def test_log1p_option_is_monotonic():
    raw = marginal_features(["Pa", "Pb"], ["G1", "G2"], _degrees(), log1p=False)
    logd = marginal_features(["Pa", "Pb"], ["G1", "G2"], _degrees(), log1p=True)
    # log1p preserves ordering but compresses scale
    assert np.argsort(logd[:, 0]).tolist() == np.argsort(raw[:, 0]).tolist()
    assert logd[0, 0] < raw[0, 0]  # 100 → log1p(100) ≈ 4.6


def _ess():
    # DepMap gene-effect convention: more negative = more essential, ~0 = non-essential.
    return {"Pa": -1.5, "G1": -0.8, "G2": 0.1}


def test_essentiality_appends_two_columns():
    X = marginal_features(["Pa", "Pb"], ["G1", "G2"], _degrees(), essentiality=_ess())
    assert X.shape == (2, 4)  # [pert_deg, gene_deg, pert_ess, gene_ess]
    assert X[0, 2] == -1.5 and X[0, 3] == -0.8
    assert X[1, 3] == 0.1


def test_essentiality_missing_symbol_is_zero():
    X = marginal_features(["Zz"], ["G2"], _degrees(), essentiality=_ess())
    assert X[0, 2] == 0.0 and X[0, 3] == 0.1  # unknown pert → 0.0 (non-essential)


def test_log1p_does_not_touch_essentiality():
    # log1p must apply only to the (non-negative) degree columns, never the signed score
    X = marginal_features(["Pa"], ["G1"], _degrees(), log1p=True, essentiality=_ess())
    assert X[0, 2] == -1.5 and X[0, 3] == -0.8  # essentiality untouched
    assert X[0, 0] == np.log1p(100)  # degree still compressed
