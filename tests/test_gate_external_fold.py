"""Tests for the external real-label fold in triple_verify (Traxler validation)."""

from __future__ import annotations

import pandas as pd

from bio_reasoning.trial_loop.gate import score_external_fold, triple_verify
from bio_reasoning.trial_loop.types import Variant

_PRED = {"up": (1.0, 0.0), "down": (0.0, 1.0), "none": (0.0, 0.0)}


def _challenge(n: int = 300) -> pd.DataFrame:
    labels = ["up", "down", "none"]
    return pd.DataFrame(
        {
            "pert": [f"p{i % 40}" for i in range(n)],
            "gene": [f"g{i % 37}" for i in range(n)],
            "label": [labels[i % 3] for i in range(n)],
        }
    )


def _external(n: int = 90) -> pd.DataFrame:
    labels = ["up", "down", "none"]
    return pd.DataFrame(
        {
            "pert": [f"ext{i % 4}" for i in range(n)],
            "gene": [f"eg{i % 30}" for i in range(n)],
            "label": [labels[i % 3] for i in range(n)],
        }
    )


def _stable_frac(pert: str, gene: str) -> float:
    return (abs(hash((pert, gene))) % 10_000) / 10_000.0


def _dual_oracle(acc):
    """acc(variant_id, is_external) -> accuracy p. Correct label for a p-fraction of rows."""

    def _pred(rows, variant, seed, get_examples):
        is_ext = bool(rows) and str(rows[0]["pert"]).startswith("ext")
        p = acc(variant.id, is_ext)
        return [
            _PRED[r["label"]] if _stable_frac(r["pert"], r["gene"]) < p else (0.0, 0.0)
            for r in rows
        ]

    return _pred


def test_score_external_fold_matches_accuracy():
    fold = _external()
    perfect = _dual_oracle(lambda vid, ext: 1.0)
    chance = _dual_oracle(lambda vid, ext: 0.0)
    assert score_external_fold(fold, Variant(id="v"), perfect) == 1.0
    assert score_external_fold(fold, Variant(id="v"), chance) == 0.5  # constant preds → AUROC 0.5


def test_accepts_when_holds_on_both_challenge_and_external():
    df, fold = _challenge(), _external()
    # candidate beats baseline on BOTH challenge-OOD and the external fold
    acc = lambda vid, ext: {"cand": 1.0, "base": 0.5}[vid]  # noqa: E731
    res = triple_verify(
        df,
        Variant(id="cand"),
        Variant(id="base"),
        _dual_oracle(acc),
        seeds=(0, 1, 2),
        noise_band=0.1,
        external_fold=fold,
    )
    assert res.accepted
    assert res.external_candidate > res.external_baseline
    assert res.external_delta > 0


def test_rejects_overfit_challenge_but_fails_external():
    df, fold = _challenge(), _external()

    # candidate wins challenge-OOD but LOSES on the real fold → overfit, must be rejected
    def acc(vid, ext):
        if vid == "base":
            return 0.5
        return 1.0 if not ext else 0.3  # cand: great on challenge, worse than base on external

    res = triple_verify(
        df,
        Variant(id="cand"),
        Variant(id="base"),
        _dual_oracle(acc),
        seeds=(0, 1, 2),
        noise_band=0.1,
        external_fold=fold,
    )
    assert not res.accepted  # passed OOD but failed the external hold
    assert res.external_delta < 0


def test_external_not_evaluated_when_ood_fails():
    df, fold = _challenge(), _external()
    # candidate no better than baseline on challenge → OOD gate fails; external short-circuited
    acc = lambda vid, ext: 0.5  # noqa: E731
    res = triple_verify(
        df,
        Variant(id="cand"),
        Variant(id="base"),
        _dual_oracle(acc),
        seeds=(0, 1, 2),
        noise_band=0.1,
        external_fold=fold,
    )
    assert not res.accepted
    assert res.external_candidate is None  # not scored — OOD already rejected it


def test_backward_compatible_without_external_fold():
    df = _challenge()
    acc = lambda vid, ext: {"cand": 1.0, "base": 0.5}[vid]  # noqa: E731
    res = triple_verify(
        df,
        Variant(id="cand"),
        Variant(id="base"),
        _dual_oracle(acc),
        seeds=(0, 1, 2),
        noise_band=0.1,
    )
    assert res.accepted and res.external_candidate is None
