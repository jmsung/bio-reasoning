"""Goal 1: CFA-gate + rank-fuse multiple DIRECTION channels.

Each direction channel supplies a per-row ``r`` (P(up)); ``fuse_direction_channels``
admits a candidate only if its ``r`` is predictive of up-vs-down on DE rows AND
diverse from the current fused direction, then rank-fuses the survivors with the
model's direction (keeping the model's DE score). Reuses the target-agnostic
``cfa_gate`` (gating ``r`` against ``is_up`` on DE rows).
"""

import numpy as np

from bio_reasoning.models.direction_fusion import fuse_direction_channels


def _labels(rng, n):
    return rng.choice(["up", "down", "none"], size=n, p=[0.3, 0.2, 0.5])


def test_admits_predictive_diverse_rejects_redundant_and_noise():
    rng = np.random.default_rng(0)
    n = 1500  # enough DE rows that a noise channel's AUROC stays tight around 0.5
    labels = _labels(rng, n)
    is_up = (labels == "up").astype(float)
    # model direction: weakly predictive of up
    model_r = 0.5 + 0.15 * is_up + rng.normal(0, 0.2, n)
    model_s_de = rng.random(n)
    # candidate A: predictive AND decorrelated from model noise → admit
    cand_a = 0.5 + 0.25 * is_up + rng.normal(0, 0.2, n)
    # candidate B: ~ model_r (redundant) → reject on diversity
    cand_b = model_r + rng.normal(0, 0.01, n)
    # candidate C: pure noise → reject on AUROC
    cand_c = rng.random(n)

    up, down, decisions = fuse_direction_channels(
        model_s_de,
        model_r,
        [("A", cand_a), ("B", cand_b), ("C", cand_c)],
        labels,
        min_auroc=0.55,
        max_abs_corr=0.7,
    )
    admitted = {name for name, passed, _ in decisions if passed}
    assert "A" in admitted
    assert "B" not in admitted  # redundant
    assert "C" not in admitted  # uninformative
    assert up.shape == down.shape == (n,)
    assert ((up >= 0) & (down >= 0)).all()


def test_de_score_is_model_only_regardless_of_direction_channels():
    rng = np.random.default_rng(1)
    n = 300
    labels = _labels(rng, n)
    model_s_de = rng.random(n)
    model_r = rng.random(n)
    up, down, _ = fuse_direction_channels(
        model_s_de, model_r, [("X", rng.random(n))], labels, min_auroc=0.0, max_abs_corr=1.0
    )
    # DE (up+down) is a rank-transform of model_s_de only → order preserved
    assert np.argsort(up + down).tolist() == np.argsort(model_s_de).tolist()


def test_no_candidates_returns_model_direction():
    rng = np.random.default_rng(2)
    n = 200
    labels = _labels(rng, n)
    model_s_de = rng.random(n)
    model_r = rng.random(n)
    up, down, decisions = fuse_direction_channels(model_s_de, model_r, [], labels)
    assert decisions == []
    # only the model channel → fused direction order matches model_r
    share = up / (up + down)
    assert np.argsort(share).tolist() == np.argsort(model_r).tolist()
