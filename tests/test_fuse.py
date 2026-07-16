"""Rank-fusion harness + CFA diversity gate (Goal 1).

The fuse harness combines any set of DE score channels by rank (scale-free,
order-preserving). The CFA (Correlation-Filtered Admission) gate only admits a
new channel when it is both *strong* (high standalone DE-AUROC) and *diverse*
(low Spearman-r vs the current fused score) — so a redundant channel is
rejected before it dilutes the fused submission.
"""

import numpy as np
import pytest

from bio_reasoning.fuse import CFAResult, cfa_gate, fuse, rank_normalize


def test_rank_normalize_is_monotone_and_bounded():
    scores = np.array([10.0, -3.0, 5.0, 5.0, 100.0])
    r = rank_normalize(scores)
    assert r.min() == 0.0 and r.max() == 1.0
    # order-preserving: argsort of ranks == argsort of scores
    assert np.array_equal(np.argsort(r, kind="stable"), np.argsort(scores, kind="stable"))
    # tied inputs get equal (average) rank
    assert r[2] == r[3]


def test_rank_normalize_single_element():
    assert rank_normalize(np.array([42.0])).tolist() == [0.0]


def test_fuse_single_channel_equals_rank_normalized():
    s = np.array([3.0, 1.0, 2.0, 9.0])
    assert np.allclose(fuse({"a": s}), rank_normalize(s))


def test_fuse_is_deterministic():
    a = np.array([1.0, 2.0, 3.0, 4.0])
    b = np.array([4.0, 1.0, 3.0, 2.0])
    f1 = fuse({"a": a, "b": b})
    f2 = fuse({"a": a, "b": b})
    assert np.array_equal(f1, f2)


def test_fuse_ranks_agreement_high():
    # A row top-ranked in BOTH channels must be the top fused row.
    a = np.array([0.1, 0.9, 0.5, 0.2])
    b = np.array([0.2, 0.8, 0.4, 0.1])
    f = fuse({"a": a, "b": b})
    assert int(np.argmax(f)) == 1


def test_fuse_weights_bias_toward_channel():
    a = np.array([0.9, 0.1, 0.5])  # row 0 top
    b = np.array([0.1, 0.9, 0.5])  # row 1 top
    heavy_a = fuse({"a": a, "b": b}, weights={"a": 3.0, "b": 1.0})
    assert int(np.argmax(heavy_a)) == 0


def test_fuse_length_mismatch_raises():
    with pytest.raises(ValueError):
        fuse({"a": np.array([1.0, 2.0]), "b": np.array([1.0])})


def test_fuse_empty_raises():
    with pytest.raises(ValueError):
        fuse({})


def _diagonal_channel(de_true, strength, rng):
    """A channel correlated with the DE label at a given strength (0..1)."""
    noise = rng.random(len(de_true))
    return strength * de_true.astype(float) + (1 - strength) * noise


def test_cfa_admits_strong_and_diverse():
    rng = np.random.default_rng(0)
    de_true = np.array([0, 1, 0, 1, 1, 0, 1, 0, 0, 1] * 4)
    # both channels are mildly predictive; independent noise keeps their mutual
    # correlation below the label-only baseline → strong but diverse.
    current = _diagonal_channel(de_true, 0.4, rng)
    candidate = _diagonal_channel(de_true, 0.45, np.random.default_rng(99))
    res = cfa_gate(candidate, current, de_true, min_auroc=0.55, max_corr=0.8)
    assert isinstance(res, CFAResult)
    assert res.admit
    assert res.de_auroc >= 0.55


def test_cfa_rejects_redundant_channel():
    rng = np.random.default_rng(1)
    de_true = np.array([0, 1, 0, 1, 1, 0, 1, 0, 0, 1] * 4)
    current = _diagonal_channel(de_true, 0.7, rng)
    candidate = current.copy()  # perfectly redundant
    res = cfa_gate(candidate, current, de_true, min_auroc=0.55, max_corr=0.8)
    assert not res.admit
    assert res.max_spearman > 0.8


def test_cfa_rejects_weak_channel():
    rng = np.random.default_rng(2)
    de_true = np.array([0, 1, 0, 1, 1, 0, 1, 0, 0, 1] * 4)
    current = _diagonal_channel(de_true, 0.7, rng)
    candidate = np.random.default_rng(7).random(len(de_true))  # chance-level
    res = cfa_gate(candidate, current, de_true, min_auroc=0.60, max_corr=0.9)
    assert not res.admit


def test_cfa_first_channel_admits_on_auroc_alone():
    de_true = np.array([0, 1, 0, 1, 1, 0, 1, 0])
    candidate = de_true.astype(float) + 0.01  # near-perfect
    res = cfa_gate(candidate, None, de_true, min_auroc=0.55, max_corr=0.8)
    assert res.admit
    assert res.max_spearman == 0.0
