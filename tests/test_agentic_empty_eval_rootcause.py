"""Root-cause guards for the agentic `n_val=0` / phantom-0.547 overnight symptom.

The overnight `--agentic` run "finished" trials showing `n_val: 0, auroc_de: nan,
auroc_dir: nan` and a `mean 0.547` that "beat" the floor — read at the time as *the
DSPy ReAct agent produced no valid predictions (empty eval)*. That diagnosis was
WRONG. This module pins the real cause:

  * The agentic eval is **non-empty** — the agent produces a full-length prediction
    array and `evaluate()` returns a real (non-nan) mean (this file, below).
  * The misleading `n_val=0` + nan AUROCs are a **reporting default**: the driver's
    `TrialRecord.metrics` never carries `n_val`/`auroc_de`/`auroc_dir`, so
    `render_leaderboard`'s `.get(..., 0/nan)` fills them in — see
    `test_driver_record_carries_val_diagnostics` (the regression that drives the fix).

A fake agent (no network) makes it deterministic and offline.
"""

from __future__ import annotations

import math

import pandas as pd

from bio_reasoning.trial_loop.archive import render_leaderboard
from bio_reasoning.trial_loop.driver import self_improve_loop
from bio_reasoning.trial_loop.loop import make_agent_row_predictor, run_variant
from bio_reasoning.trial_loop.reflect import make_grid_proposer
from bio_reasoning.trial_loop.types import Variant


def _frame(n: int = 240) -> pd.DataFrame:
    labels = ["up", "down", "none"]
    return pd.DataFrame(
        {
            "pert": [f"p{i % 30}" for i in range(n)],
            "gene": [f"g{i % 29}" for i in range(n)],
            "label": [labels[i % 3] for i in range(n)],
        }
    )


def _varied_agent(pert: str, gene: str, seed: int) -> tuple[float, float]:
    """A fake agent that returns valid, VARIED up/down for every row (real signal)."""
    h = (abs(hash((pert, gene))) % 100) / 100.0
    return (h, 1.0 - h)


def test_agentic_eval_is_nonempty_with_real_score():
    """The agentic lane scores a full, non-empty val set — the 'empty eval' was a misread.

    Drives the same run_variant path the gate uses; asserts a positive n_val and a real
    (non-nan) mean, so 'no valid predictions for any val row' is refuted at the source.
    """
    df = _frame()
    predictor = make_agent_row_predictor(_varied_agent)
    variant = Variant(id="agent-go-s1", tools=("go_terms",), seeds=(42,))

    rec = run_variant(df, variant, predictor, seed=0)

    assert rec.metrics["n_val"] > 0, "agentic val set is non-empty — not an empty eval"
    assert not math.isnan(rec.metrics["mean"]), "a non-empty eval yields a real mean"


def _run_loop():
    df = _frame()
    predictor = make_agent_row_predictor(_varied_agent)
    return self_improve_loop(
        df,
        make_grid_proposer([Variant(id="agent-go-s1", tools=("go_terms",), seeds=(42,))]),
        predictor,
        Variant(id="agent-prior-s1", tools=(), seeds=(42,)),
        seeds=(0, 1, 2),
        noise_band=0.05,
        max_trials=1,
    )


def test_driver_record_carries_val_diagnostics():
    """The driver record must carry real n_val + AUROCs — not the 0/nan defaults.

    This is the regression for the phantom: before the fix the driver stored only
    {mean, baseline_mean, min_margin, feasibility_ratio, accepted}, so these keys were
    absent and the leaderboard filled them with 0/nan — the false 'empty eval' signal.
    """
    rec = _run_loop().records[0]
    assert rec.metrics["n_val"] > 0
    assert not math.isnan(rec.metrics["auroc_de"])
    assert not math.isnan(rec.metrics["auroc_dir"])


def test_leaderboard_shows_real_n_val_not_zero():
    """render_leaderboard must not report a healthy trial as n_val=0."""
    table = render_leaderboard(_run_loop().records)
    # the n_val column is the real val-set size (240 rows, ~40% held out), never 0
    assert "| 0 |" not in table, f"leaderboard still shows n_val=0:\n{table}"
