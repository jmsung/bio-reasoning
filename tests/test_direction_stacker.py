"""Goal 2: a learned combiner over the direction channels' per-row r.

Tests that stacking complementary channels beats the best single channel, that
NaN (uncovered) rows are handled, and that the fitted model predicts P(up) in
[0, 1]. Leak-free evaluation (out-of-fold) is the caller's job — see
`scripts/weighted_direction_fuse.py`.
"""

import numpy as np
from sklearn.metrics import roc_auc_score

from bio_reasoning.models.direction_stacker import DirectionStacker


def _complementary(n=400):
    """3 weak, independent noisy views of one latent direction → combining should win."""
    rng = np.random.default_rng(0)
    latent = rng.normal(size=n)
    is_up = (latent > 0).astype(int)
    cols = [np.clip(0.5 + 0.15 * latent + 0.30 * rng.normal(size=n), 0, 1) for _ in range(3)]
    return np.column_stack(cols), is_up


def test_stacker_beats_best_single_on_complementary_channels():
    R, is_up = _complementary()
    tr, te = slice(0, 300), slice(300, None)
    stacker = DirectionStacker().fit(R[tr], is_up[tr])
    pred = stacker.predict_up(R[te])
    assert pred.shape == (R[te].shape[0],)
    assert np.all((pred >= 0) & (pred <= 1))
    auc_stack = roc_auc_score(is_up[te], pred)
    auc_best_single = max(roc_auc_score(is_up[te], R[te, j]) for j in range(3))
    assert auc_stack > auc_best_single  # combining 3 noisy views beats any one


def test_stacker_handles_nan_uncovered_rows():
    R, is_up = _complementary(n=200)
    R[::5, 1] = np.nan  # neighbour-DIR uncovered on some rows
    stacker = DirectionStacker().fit(R, is_up)
    pred = stacker.predict_up(R)
    assert np.all(np.isfinite(pred))  # NaN imputed, no propagation
    assert np.all((pred >= 0) & (pred <= 1))
