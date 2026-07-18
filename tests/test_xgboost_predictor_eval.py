"""Tests for the XGBoost two-stage predictor core (scripts/xgboost_predictor_eval.py).

The script is a measurement harness, not library code, so it is loaded by path.
These guard the one genuinely new piece of logic — the ``P(DE) * P(up|DE)`` two-stage
wrapper around ``XGBClassifier`` — including the degenerate single-direction train fold
that ``_fit_p_positive`` must handle without crashing (XGBoost rejects an all-``1``
single-class ``y`` at fit time).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "xgboost_predictor_eval.py"
_spec = importlib.util.spec_from_file_location("xgboost_predictor_eval", _SCRIPT)
assert _spec and _spec.loader
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def _toy(n: int = 60, seed: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Small synthetic set with a learnable DE signal in column 0."""
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, 4))
    y_de = (x[:, 0] > 0).astype(int)
    y_up = (x[y_de == 1, 1] > 0).astype(int)
    return x, y_de, y_up


def test_two_stage_shapes_and_range() -> None:
    x, y_de, y_up = _toy()
    up, down = mod.xgb_two_stage(x, y_de, y_up, x, seed=0)
    assert up.shape == (len(x),)
    assert down.shape == (len(x),)
    # up = P(DE)*P(up), down = P(DE)*(1-P(up)); both in [0,1], sum = P(DE) <= 1.
    assert np.all(up >= 0) and np.all(up <= 1)
    assert np.all(down >= 0) and np.all(down <= 1)
    assert np.all(up + down <= 1.0 + 1e-9)


def test_two_stage_recovers_de_signal() -> None:
    # Column 0 fully determines DE; the P(DE) ranking (up+down) should separate classes.
    x, y_de, y_up = _toy(n=120)
    up, down = mod.xgb_two_stage(x, y_de, y_up, x, seed=0)
    p_de = up + down
    assert p_de[y_de == 1].mean() > p_de[y_de == 0].mean()


def test_degenerate_single_direction_fold() -> None:
    # All DE rows share one direction → the dir head sees a single class (all 1s, which
    # XGBoost rejects at fit time); _fit_p_positive must short-circuit, not crash.
    x, y_de, _ = _toy()
    y_up_const = np.ones(int(y_de.sum()), dtype=int)
    up, down = mod.xgb_two_stage(x, y_de, y_up_const, x, seed=0)
    assert up.shape == (len(x),)
    # p_up == 1 everywhere → down (=P(DE)*(1-p_up)) collapses to ~0.
    assert np.allclose(down, 0.0, atol=1e-6)


def test_fit_p_positive_single_class() -> None:
    x = np.random.default_rng(0).normal(size=(20, 3))
    # Only class 0 present → P(class==1) = 0 everywhere; only class 1 → 1 everywhere.
    zeros = mod._fit_p_positive(x, np.zeros(20, dtype=int), x, seed=0)
    ones = mod._fit_p_positive(x, np.ones(20, dtype=int), x, seed=0)
    assert np.allclose(zeros, 0.0)
    assert np.allclose(ones, 1.0)
