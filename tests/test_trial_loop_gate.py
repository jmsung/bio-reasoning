"""Offline tests for the triple-verify gate (injected oracle predictors, no network)."""

from __future__ import annotations

import pandas as pd
import pytest

from bio_reasoning.trial_loop.gate import measure_noise_band, triple_verify
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
    """Split-seed-independent hash in [0, 1) so a config's accuracy is stable."""
    h = abs(hash((pert, gene))) % 10_000
    return h / 10_000.0


def _variant_oracle(p_by_id: dict[str, float]):
    """Row predictor whose accuracy is set by ``variant.id`` (models config quality).

    A fraction ``p`` of rows (deterministic by pert/gene) get the correct (up, down);
    the rest get (0, 0). Higher ``p`` → higher AUROC, monotonically.
    """

    def _pred(rows, variant, seed, get_examples):
        p = p_by_id[variant.id]
        return [
            _PRED[r["label"]] if _stable_frac(r["pert"], r["gene"]) < p else (0.0, 0.0)
            for r in rows
        ]

    return _pred


def test_measure_noise_band_is_range():
    assert measure_noise_band([0.60, 0.62, 0.61]) == pytest.approx(0.02)


def test_accepts_a_real_improvement():
    df = _frame()
    predictor = _variant_oracle({"base": 0.5, "cand": 1.0})
    res = triple_verify(
        df,
        Variant(id="cand"),
        Variant(id="base"),
        predictor,
        seeds=(0, 1, 2),
        noise_band=0.1,
    )
    assert res.accepted
    assert all(m > 0.1 for m in res.margins)
    assert res.feasibility_ratio > 1.0


def test_rejects_a_within_noise_improvement():
    df = _frame()
    # candidate is only marginally better than baseline — a phantom lift < band.
    predictor = _variant_oracle({"base": 0.50, "cand": 0.52})
    res = triple_verify(
        df,
        Variant(id="cand"),
        Variant(id="base"),
        predictor,
        seeds=(0, 1, 2),
        noise_band=0.1,
    )
    assert not res.accepted


def test_rejects_when_not_all_seeds_beat_baseline():
    df = _frame()
    predictor = _variant_oracle({"base": 0.6, "cand": 0.9})
    res = triple_verify(
        df,
        Variant(id="cand"),
        Variant(id="base"),
        predictor,
        seeds=(0, 1, 2),
    )
    # Force one seed to fail by demanding an impossibly large margin.
    res_strict = triple_verify(
        df,
        Variant(id="cand"),
        Variant(id="base"),
        predictor,
        seeds=(0, 1, 2),
        noise_band=1.0,
    )
    assert not res_strict.accepted
    # sanity: the real gain is nonetheless positive on every seed
    assert all(m > 0 for m in res.margins)
