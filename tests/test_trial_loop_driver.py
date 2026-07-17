"""Offline tests for the self-improvement loop driver (injected predictors, no network)."""

from __future__ import annotations

import pandas as pd

from bio_reasoning.trial_loop.driver import self_improve_loop
from bio_reasoning.trial_loop.reflect import make_grid_proposer
from bio_reasoning.trial_loop.types import Variant

_PRED = {"up": (1.0, 0.0), "down": (0.0, 1.0), "none": (0.0, 0.0)}


def _frame(n: int = 300) -> pd.DataFrame:
    labels = ["up", "down", "none"]
    return pd.DataFrame(
        {
            "pert": [f"p{i % 40}" for i in range(n)],
            "gene": [f"g{i % 37}" for i in range(n)],
            "label": [labels[i % 3] for i in range(n)],
        }
    )


def _stable_frac(pert: str, gene: str) -> float:
    return (abs(hash((pert, gene))) % 10_000) / 10_000.0


def _variant_oracle(p_by_id: dict[str, float]):
    def _pred(rows, variant, seed, get_examples):
        p = p_by_id[variant.id]
        return [
            _PRED[r["label"]] if _stable_frac(r["pert"], r["gene"]) < p else (0.0, 0.0)
            for r in rows
        ]

    return _pred


def test_promotes_accepted_and_stops_dry():
    df = _frame()
    base = Variant(id="base")
    cands = [Variant(id="strong"), Variant(id="weak1"), Variant(id="weak2")]
    predictor = _variant_oracle({"base": 0.5, "strong": 1.0, "weak1": 0.51, "weak2": 0.52})
    res = self_improve_loop(
        df,
        make_grid_proposer(cands),
        predictor,
        base,
        seeds=(0, 1, 2),
        noise_band=0.1,
        dry_rounds=2,
    )
    assert [v.id for v in res.accepted] == ["strong"]
    assert res.baseline.id == "strong"  # promoted
    assert res.stopped_reason == "dry"
    assert len(res.records) == 3


def test_stops_on_budget():
    df = _frame(120)
    calls = {"n": 0}

    def counting_predictor(rows, variant, seed, get_examples):
        calls["n"] += len(rows)
        return [(0.0, 0.0) for _ in rows]

    def spent_fn() -> float:
        return float(calls["n"])

    res = self_improve_loop(
        df,
        make_grid_proposer([Variant(id="a"), Variant(id="b"), Variant(id="c")]),
        counting_predictor,
        Variant(id="base"),
        seeds=(0, 1, 2),
        noise_band=0.1,
        budget=1.0,
        spent_fn=spent_fn,
    )
    assert res.stopped_reason == "budget"
    assert res.spent > 0
    assert len(res.records) >= 1  # at least one candidate evaluated before the cap tripped


def test_converges_when_grid_exhausted():
    df = _frame()
    predictor = _variant_oracle({"base": 0.5, "a": 1.0})
    res = self_improve_loop(
        df,
        make_grid_proposer([Variant(id="a")]),
        predictor,
        Variant(id="base"),
        seeds=(0, 1, 2),
        noise_band=0.1,
        dry_rounds=5,
    )
    assert res.stopped_reason == "converged"
    assert [v.id for v in res.accepted] == ["a"]
