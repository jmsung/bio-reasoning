"""Offline tests for trial-loop archiving (Goal 3)."""

from __future__ import annotations

import json

from bio_reasoning.trial_loop.archive import (
    archive,
    leaderboard,
    load_trials,
    render_leaderboard,
    write_trials,
)
from bio_reasoning.trial_loop.types import TrialRecord, Variant


def _rec(vid: str, mean: float, n_few_shot: int = 0) -> TrialRecord:
    return TrialRecord(
        variant=Variant(id=vid, n_few_shot=n_few_shot),
        metrics={"auroc_de": mean, "auroc_dir": mean, "mean": mean, "n_val": 200},
        cost_usd=0.01,
    )


def test_trials_jsonl_round_trip(tmp_path) -> None:
    path = tmp_path / "trials.jsonl"
    recs = [_rec("a", 0.52), _rec("b", 0.58, n_few_shot=4)]
    write_trials(path, recs)
    assert load_trials(path) == recs


def test_load_trials_missing_returns_empty(tmp_path) -> None:
    assert load_trials(tmp_path / "nope.jsonl") == []


def test_leaderboard_sorts_by_mean_nan_last() -> None:
    board = leaderboard([_rec("a", 0.52), _rec("nan", float("nan")), _rec("b", 0.58)])
    assert [r.variant.id for r in board] == ["b", "a", "nan"]


def test_render_leaderboard_has_header_and_best_first() -> None:
    md = render_leaderboard([_rec("a", 0.52), _rec("b", 0.58)])
    assert "| rank | variant |" in md
    lines = [ln for ln in md.splitlines() if ln.startswith("| 1 ")]
    assert "b" in lines[0]  # best variant ranked first


def test_archive_writes_leaderboard_and_best_variant(tmp_path) -> None:
    history = [_rec("a", 0.52), _rec("b", 0.58, n_few_shot=4)]
    paths = archive(tmp_path, history)

    assert paths["leaderboard"].exists() and paths["best_variant"].exists()
    best = json.loads(paths["best_variant"].read_text())
    assert best["id"] == "b" and best["n_few_shot"] == 4
    assert "0.580" in paths["leaderboard"].read_text()
