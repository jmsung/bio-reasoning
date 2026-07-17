"""Offline tests for the loop preflight harness (no network; fake infer_fn).

Codifies the loop deadlock / throughput-verification lesson: a loop is 'verified'
only on real content + a real archived trial, never on liveness. Each
degenerate mode (empty responses, nan mean, n_val=0, no archive) must fail loud.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from bio_reasoning.trial_loop.preflight import (
    PreflightError,
    assert_healthy,
    run_preflight,
)
from bio_reasoning.trial_loop.types import TrialRecord, Variant

_UP, _DOWN = "upregulated", "downregulated"


def _frame(n: int = 120) -> pd.DataFrame:
    labels = ["up", "down", "none"]
    return pd.DataFrame(
        {
            "pert": [f"p{i % 30}" for i in range(n)],
            "gene": [f"g{i % 60}" for i in range(n)],
            "label": [labels[i % 3] for i in range(n)],
        }
    )


def _healthy_record() -> TrialRecord:
    return TrialRecord(variant=Variant(id="v"), metrics={"mean": 0.55, "n_val": 40})


# --- assert_healthy: one degenerate mode per test -------------------------------


def test_assert_healthy_passes_on_real_trial(tmp_path) -> None:
    (tmp_path / "leaderboard.md").write_text("x")
    (tmp_path / "best_variant.json").write_text("{}")
    assert_healthy(_healthy_record(), tmp_path, nonempty_responses=40)  # no raise


def test_assert_healthy_fails_on_empty_responses(tmp_path) -> None:
    (tmp_path / "leaderboard.md").write_text("x")
    (tmp_path / "best_variant.json").write_text("{}")
    with pytest.raises(PreflightError, match="empty"):
        assert_healthy(_healthy_record(), tmp_path, nonempty_responses=0)


def test_assert_healthy_fails_on_zero_n_val(tmp_path) -> None:
    (tmp_path / "leaderboard.md").write_text("x")
    (tmp_path / "best_variant.json").write_text("{}")
    rec = TrialRecord(variant=Variant(id="v"), metrics={"mean": 0.55, "n_val": 0})
    with pytest.raises(PreflightError, match="n_val"):
        assert_healthy(rec, tmp_path, nonempty_responses=40)


def test_assert_healthy_fails_on_nan_mean(tmp_path) -> None:
    (tmp_path / "leaderboard.md").write_text("x")
    (tmp_path / "best_variant.json").write_text("{}")
    rec = TrialRecord(variant=Variant(id="v"), metrics={"mean": float("nan"), "n_val": 40})
    with pytest.raises(PreflightError, match="nan"):
        assert_healthy(rec, tmp_path, nonempty_responses=40)


def test_assert_healthy_fails_on_missing_archive(tmp_path) -> None:
    with pytest.raises(PreflightError, match="archive"):
        assert_healthy(_healthy_record(), tmp_path, nonempty_responses=40)


# --- run_preflight end-to-end (fake infer_fn) -----------------------------------


def test_run_preflight_green_on_healthy_infer(tmp_path) -> None:
    """A healthy infer_fn → non-empty responses, real mean, n_val>0, archive written."""

    def infer(prompts, seed):
        return [_UP if i % 2 == 0 else _DOWN for i in range(len(prompts))]

    rec = run_preflight(_frame(), infer, tmp_path, val_n=15)
    assert rec.metrics["n_val"] == 15
    assert not math.isnan(rec.metrics["mean"])
    assert (tmp_path / "leaderboard.md").is_file()
    assert (tmp_path / "best_variant.json").is_file()


def test_run_preflight_red_on_empty_responses(tmp_path) -> None:
    """The auth-401 / dead-endpoint mode: every response empty → fail loud."""

    def infer(prompts, seed):
        return ["" for _ in prompts]

    with pytest.raises(PreflightError, match="empty"):
        run_preflight(_frame(), infer, tmp_path, val_n=30)


def test_run_preflight_red_on_zero_val(tmp_path) -> None:
    """val_n=0 → the scorer sees no rows → fail loud (never a silent nan trial)."""

    def infer(prompts, seed):
        return [_UP for _ in prompts]

    with pytest.raises(PreflightError):
        run_preflight(_frame(), infer, tmp_path, val_n=0)
