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
