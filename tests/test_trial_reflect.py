"""Offline tests for the trial-loop reflection + proposer (Goal 2)."""

from __future__ import annotations

from bio_reasoning.trial_loop.reflect import best_trial, make_grid_proposer, reflect
from bio_reasoning.trial_loop.types import TrialRecord, Variant


def _rec(vid: str, mean: float) -> TrialRecord:
    return TrialRecord(
        variant=Variant(id=vid),
        metrics={"auroc_de": mean, "auroc_dir": mean, "mean": mean, "n_val": 100},
    )


def test_reflect_empty() -> None:
    assert reflect([]) == "No trials yet."


def test_reflect_summarizes_means_and_best() -> None:
    text = reflect([_rec("a", 0.52), _rec("b", 0.58)])
    assert "variant=a" in text and "0.520" in text
    assert "variant=b" in text and "0.580" in text
    assert "best" in text and "variant=b" in text.splitlines()[-1]
    assert "+0.06" in text  # delta of b over the running best (a)


def test_best_trial_is_nan_safe() -> None:
    history = [_rec("a", 0.55), _rec("nanv", float("nan")), _rec("b", 0.51)]
    best = best_trial(history)
    assert best.variant.id == "a"


def test_grid_proposer_walks_untried_then_exhausts() -> None:
    cands = [Variant(id="v0"), Variant(id="v1"), Variant(id="v2")]
    propose = make_grid_proposer(cands)

    history: list[TrialRecord] = []
    proposed_ids = []
    for _ in range(4):
        nxt = propose(reflect(history), history)
        if nxt is None:
            break
        proposed_ids.append(nxt.id)
        history.append(_rec(nxt.id, 0.5))
    assert proposed_ids == ["v0", "v1", "v2"]
    assert propose(reflect(history), history) is None  # exhausted


def test_reflect_marks_regression() -> None:
    text = reflect([_rec("a", 0.60), _rec("b", 0.55)])
    # b is worse than the running best → negative delta shown.
    assert "-0.05" in text
