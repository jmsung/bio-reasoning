"""Tests for self-consistency aggregation of per-(pert, gene) DE answers.

Kill-test apparatus for feat/de-logprob-self-consistency: the KB predicts the DE
axis is near-chance under dual-OOD (AUROC_de ~= 0.50), so this exists to *measure*
whether sampled / logprob self-consistency escapes chance, not to assume it does.
"""

from __future__ import annotations

import math

import pytest

from bio_reasoning.models.de_logprob import logprobs_to_scores, votes_to_scores


def test_votes_to_scores_basic_fractions() -> None:
    p_up, p_down, p_none = votes_to_scores(["up", "up", "down", "none", "up"])
    assert p_up == pytest.approx(0.6)
    assert p_down == pytest.approx(0.2)
    assert p_none == pytest.approx(0.2)
    # metric consumes graded floats: DE score = up + down, dir score = up/(up+down)
    assert (p_up + p_down) == pytest.approx(0.8)


def test_votes_to_scores_normalizes_and_ignores_unparseable() -> None:
    # unparseable votes ("maybe", "") drop out of the denominator
    p_up, p_down, p_none = votes_to_scores(["UP", " Down ", "maybe", ""])
    assert (p_up, p_down, p_none) == pytest.approx((0.5, 0.5, 0.0))


def test_votes_to_scores_all_invalid_is_none() -> None:
    # no valid votes -> treat as "none" (DE score 0), never divide by zero
    assert votes_to_scores(["", "xyz"]) == pytest.approx((0.0, 0.0, 1.0))
    assert votes_to_scores([]) == pytest.approx((0.0, 0.0, 1.0))


def test_logprobs_to_scores_softmax_over_three_tokens() -> None:
    # equal logprobs -> uniform
    p = logprobs_to_scores({"up": -1.0, "down": -1.0, "none": -1.0})
    assert p == pytest.approx((1 / 3, 1 / 3, 1 / 3))


def test_logprobs_to_scores_orders_by_logprob() -> None:
    p_up, p_down, p_none = logprobs_to_scores({"up": -0.1, "down": -2.0, "none": -1.0})
    assert p_up > p_none > p_down
    assert (p_up + p_down + p_none) == pytest.approx(1.0)


def test_logprobs_to_scores_missing_token_gets_floor() -> None:
    # a candidate absent from top_logprobs is treated as very unlikely, not crashy
    p_up, p_down, p_none = logprobs_to_scores({"up": -0.1})
    assert p_up > 0.99
    assert p_down < 0.01 and p_none < 0.01
    assert not any(math.isnan(x) for x in (p_up, p_down, p_none))
