"""Goal 1: rank-fusion harness + CFA diversity gate.

Channels contribute a DE score (``s_de``) and/or a direction score (``r``) per
row, with ``NaN`` marking rows the channel does not cover. ``fuse`` rank-normalizes
and averages them into ``(up, down)`` the Track A scorer consumes; ``cfa_gate``
decides whether a new channel is individually predictive AND diverse enough to add.
"""

import numpy as np
import pytest
from sklearn.metrics import roc_auc_score

from bio_reasoning.models.fuse import Channel, cfa_gate, fuse


def test_fuse_single_channel_is_rank_monotonic():
    s_de = np.array([0.1, 0.9, 0.4, 0.7])
    r = np.array([0.2, 0.8, 0.5, 0.6])
    up, down = fuse([Channel("c", s_de=s_de, r=r)])
    assert up.shape == down.shape == (4,)
    # up + down = fused s_de; ordering follows s_de ranks
    s_de_fused = up + down
    assert np.argsort(s_de_fused).tolist() == np.argsort(s_de).tolist()
    # direction share up/(up+down) follows r ranks
    share = up / (up + down)
    assert np.argsort(share).tolist() == np.argsort(r).tolist()
    assert ((up >= 0) & (down >= 0)).all()


def test_fuse_nan_rows_fall_back_to_neutral():
    # channel covers no rows → fused s_de/r are neutral 0.5, up==down==0.25
    n = 5
    nan = np.full(n, np.nan)
    up, down = fuse([Channel("empty", s_de=nan, r=nan)])
    assert np.allclose(up, 0.25)
    assert np.allclose(down, 0.25)


def test_fuse_uncovered_row_uses_covering_channel():
    # row 0 covered only by channel A; row 1 only by channel B
    a = Channel("a", s_de=np.array([0.9, np.nan]), r=np.array([0.9, np.nan]))
    b = Channel("b", s_de=np.array([np.nan, 0.1]), r=np.array([np.nan, 0.1]))
    up, down = fuse([a, b])
    # both rows get a single-channel (rank-normed to 0.5 since one finite value) signal,
    # never NaN
    assert np.isfinite(up).all() and np.isfinite(down).all()


def test_fuse_added_channel_lifts_de_auroc():
    rng = np.random.default_rng(0)
    n = 400
    de_true = rng.integers(0, 2, n)
    # base channel: weak DE signal; new channel: strong, complementary DE signal
    base_s = de_true * 0.2 + rng.normal(0, 1.0, n)
    new_s = de_true * 2.0 + rng.normal(0, 1.0, n)
    r = rng.random(n)
    base_up, base_down = fuse([Channel("base", s_de=base_s, r=r)])
    fused_up, fused_down = fuse(
        [Channel("base", s_de=base_s, r=r), Channel("new", s_de=new_s, r=r)]
    )
    base_auroc = roc_auc_score(de_true, base_up + base_down)
    fused_auroc = roc_auc_score(de_true, fused_up + fused_down)
    assert fused_auroc > base_auroc


def test_fuse_weights_bias_toward_channel():
    s_a = np.array([0.9, 0.1, 0.5])
    s_b = np.array([0.1, 0.9, 0.5])
    r = np.array([0.5, 0.5, 0.5])
    up_w, _ = fuse([Channel("a", s_de=s_a, r=r), Channel("b", s_de=s_b, r=r)], weights=[0.9, 0.1])
    s_fused = up_w * 2  # r=0.5 → s_de_fused == 2*up
    assert s_fused[0] > s_fused[1]  # a dominates → row 0 ranks above row 1


def test_cfa_gate_accepts_predictive_and_diverse():
    rng = np.random.default_rng(1)
    n = 300
    de_true = rng.integers(0, 2, n)
    current = de_true * 1.0 + rng.normal(0, 1.0, n)
    # candidate: predictive of DE but decorrelated from `current`'s noise
    candidate = de_true * 1.0 + rng.normal(0, 1.0, n)
    passed, stats = cfa_gate(candidate, current, de_true, min_auroc=0.6, max_abs_corr=0.6)
    assert passed
    assert stats["auroc"] > 0.6


def test_cfa_gate_rejects_redundant_channel():
    rng = np.random.default_rng(2)
    n = 300
    de_true = rng.integers(0, 2, n)
    current = de_true * 1.0 + rng.normal(0, 1.0, n)
    candidate = current.copy()  # perfectly redundant
    passed, stats = cfa_gate(candidate, current, de_true, min_auroc=0.5, max_abs_corr=0.8)
    assert not passed
    assert stats["corr"] > 0.8


def test_cfa_gate_rejects_uninformative_channel():
    rng = np.random.default_rng(3)
    n = 300
    de_true = rng.integers(0, 2, n)
    current = de_true * 1.0 + rng.normal(0, 1.0, n)
    candidate = rng.normal(0, 1.0, n)  # pure noise → AUROC ~0.5
    passed, stats = cfa_gate(candidate, current, de_true, min_auroc=0.6, max_abs_corr=0.9)
    assert not passed
    assert stats["auroc"] < 0.6


def test_cfa_gate_partial_coverage_scores_covered_rows():
    rng = np.random.default_rng(4)
    n = 300
    de_true = rng.integers(0, 2, n)
    current = rng.normal(0, 1.0, n)
    candidate = np.full(n, np.nan)
    covered = slice(0, 150)
    candidate[covered] = de_true[covered] * 2.0 + rng.normal(0, 0.5, 150)
    passed, stats = cfa_gate(candidate, current, de_true, min_auroc=0.6, max_abs_corr=0.6)
    assert passed
    assert stats["n_covered"] == 150


def test_cfa_gate_single_class_labels_reject():
    # AUROC is undefined (NaN) when de_true has one class; the gate must reject
    # rather than admit on NaN. (Salvaged from the abandoned de-detector-fuse-harness.)
    de_true = np.ones(8, dtype=int)
    candidate = np.arange(8, dtype=float)
    passed, stats = cfa_gate(candidate, np.arange(8, dtype=float), de_true, min_auroc=0.55)
    assert not passed
    assert np.isnan(stats["auroc"])


def test_fuse_requires_at_least_one_channel():
    with pytest.raises(ValueError):
        fuse([])
