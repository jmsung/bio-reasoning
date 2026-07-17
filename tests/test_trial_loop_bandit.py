"""Offline tests for the UCB bandit policy proposer (no network; synthetic reward)."""

from __future__ import annotations

from bio_reasoning.trial_loop.bandit import make_bandit_proposer
from bio_reasoning.trial_loop.types import TrialRecord, Variant


def _rec(vid: str, reward: float) -> TrialRecord:
    return TrialRecord(variant=Variant(id=vid), metrics={"mean": reward})


def _run(proposer, samples: dict[str, list[float]], n_trials: int):
    """Simulate the loop: propose → reward = next sample for that arm → append."""
    history: list[TrialRecord] = []
    counts: dict[str, int] = {}
    for _ in range(n_trials):
        v = proposer("", history)
        if v is None:
            break
        k = counts.get(v.id, 0)
        counts[v.id] = k + 1
        history.append(_rec(v.id, samples[v.id][k]))
    return history, counts


def _arms(*ids: str) -> list[Variant]:
    return [Variant(id=i) for i in ids]


def test_denylist_filtered_never_proposes_ruled_out():
    arms = _arms("de-votes-a", "string-degree-de", "de-votes-b")  # middle one is ruled out
    proposer = make_bandit_proposer(arms)
    samples = {"de-votes-a": [0.6] * 30, "de-votes-b": [0.5] * 30}
    _, counts = _run(proposer, samples, 20)
    assert "string-degree-de" not in counts  # never pulled


def test_concentrates_pulls_on_the_best_arm():
    arms = _arms("de-votes-a", "de-votes-b", "de-votes-c")
    samples = {"de-votes-a": [0.9] * 60, "de-votes-b": [0.5] * 60, "de-votes-c": [0.5] * 60}
    proposer = make_bandit_proposer(arms, c=0.5, seed=0)
    _, counts = _run(proposer, samples, 40)
    best = max(counts, key=lambda k: counts[k])
    assert best == "de-votes-a"
    assert counts["de-votes-a"] > 40 / 3  # more than uniform allocation


def test_robust_to_noise_where_single_sample_grid_is_fooled():
    # B gets a lucky first sample (0.8) that fools a try-each-once grid; A is the true best.
    arms = _arms("A", "B", "C")
    samples = {"A": [0.6] * 40, "B": [0.8] + [0.4] * 40, "C": [0.5] * 40}
    # grid = one pull each → empirical best is B (0.8), the WRONG arm.
    grid_best = max(("A", "B", "C"), key=lambda a: samples[a][0])
    assert grid_best == "B"
    proposer = make_bandit_proposer(arms, c=0.7, seed=0)
    history, counts = _run(proposer, samples, 40)
    # bandit resamples B, its mean regresses to 0.4; A's stays 0.6 → bandit's best is A.
    means = {
        a: sum(r.metrics["mean"] for r in history if r.variant.id == a) / counts[a] for a in counts
    }
    assert max(means, key=lambda a: means[a]) == "A"


def test_max_pulls_stops_the_policy():
    arms = _arms("de-votes-a", "de-votes-b")
    samples = {"de-votes-a": [0.6] * 30, "de-votes-b": [0.5] * 30}
    proposer = make_bandit_proposer(arms, max_pulls=5)
    history, _ = _run(proposer, samples, 50)
    assert len(history) == 5  # stopped at the pull budget
