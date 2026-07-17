"""Tests for proposer selection (grid | bandit | llm) used by the runner flag."""

from __future__ import annotations

import pytest

from bio_reasoning.trial_loop.proposers import select_proposer
from bio_reasoning.trial_loop.types import TrialRecord, Variant


def test_grid_and_bandit_propose_a_live_variant():
    for name in ("grid", "bandit"):
        proposer = select_proposer(name)
        v = proposer("", [])
        assert isinstance(v, Variant) and v.id.startswith("de-votes-")


def test_llm_uses_propose_fn_then_falls_back_to_bandit():
    proposer = select_proposer(
        "llm", propose_fn=lambda r: '{"n_few_shot": 2, "retrieval": "random", "n_samples": 3}'
    )
    assert proposer("", []).id == "llm-nfs2-random-s3"
    # malformed → falls back to the bandit (a de-votes- grid arm)
    bad = select_proposer("llm", propose_fn=lambda r: "no json here")
    assert bad("", []).id.startswith("de-votes-")


def test_llm_without_propose_fn_raises():
    with pytest.raises(ValueError, match="propose_fn"):
        select_proposer("llm")


def test_unknown_proposer_raises():
    with pytest.raises(ValueError, match="unknown proposer"):
        select_proposer("telepathy")


def test_bandit_resamples_not_just_walks_once():
    # after all grid arms pulled once, the bandit re-proposes (exploits) rather than stopping
    proposer = select_proposer("bandit")
    history: list[TrialRecord] = []
    seen_ids = set()
    for _ in range(40):
        v = proposer("", history)
        assert v is not None  # bandit never converges on its own (driver stops it)
        seen_ids.add(v.id)
        history.append(TrialRecord(variant=v, metrics={"mean": 0.5}))
    assert len(history) == 40 and len(seen_ids) < 40  # some arms pulled more than once
