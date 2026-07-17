"""Regression guards for the overnight failures (fix/loop-inference-deadlock).

Two bugs, two classes of guard:
  1. Empty eval -> loud failure (was: nan-mean phantom "win" at n_val=0, agentic lane).
  2. HTTP keep-alive pileup -> the poster must send ``Connection: close`` (the leak that
     deadlocked the inference ThreadPoolExecutor under the sustained run).
Plus a loop-completion guard that drives the REAL threaded inference path (inference.py's
ThreadPoolExecutor) with a fake poster — no network — so a future orchestration deadlock
is caught offline. It does NOT reproduce the urllib keep-alive hang itself (that needs the
real endpoint; confirmed by the attended pre-flight), but it locks the threading path.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd
import pytest

from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.trial_loop.driver import self_improve_loop
from bio_reasoning.trial_loop.inference import make_openrouter_infer_fn
from bio_reasoning.trial_loop.loop import make_prompt_row_predictor
from bio_reasoning.trial_loop.reflect import make_grid_proposer
from bio_reasoning.trial_loop.types import Variant


def test_evaluate_empty_raises():
    """An empty eval must fail loud, not return a nan-mean phantom score."""
    with pytest.raises(ValueError, match="0 rows"):
        evaluate(np.array([]), np.array([]), np.array([]))


def test_evaluate_nonempty_still_scores():
    """Guard doesn't break the normal path."""
    out = evaluate(
        np.array(["up", "none", "down"]), np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0])
    )
    assert set(out) == {"auroc_de", "auroc_dir", "mean"}


def test_poster_sends_connection_close(monkeypatch):
    """post_chat_completion must set Connection: close (kills the keep-alive leak)."""
    from bio_reasoning.utils import openai_compat

    captured = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"choices":[{"message":{"content":"up"}}],"usage":{}}'

    def _fake_urlopen(req, timeout):
        captured["headers"] = {k.lower(): v for k, v in req.header_items()}
        return _Resp()

    monkeypatch.setattr(openai_compat.urllib.request, "urlopen", _fake_urlopen)
    openai_compat.post_chat_completion(
        api_base="http://x", api_key="k", model="m", prompt="p", seed=1, max_tokens=8, timeout_s=5
    )
    assert captured["headers"].get("Connection".lower()) == "close"


def _frame(n: int = 240) -> pd.DataFrame:
    labels = ["up", "down", "none"]
    return pd.DataFrame(
        {
            "pert": [f"p{i % 30}" for i in range(n)],
            "gene": [f"g{i % 29}" for i in range(n)],
            "label": [labels[i % 3] for i in range(n)],
        }
    )


def test_loop_completes_under_concurrency():
    """The real threaded inference path (ThreadPoolExecutor, concurrency>=4) completes.

    Drives make_openrouter_infer_fn's pool with a fake poster (tiny sleep, no network)
    across a full loop run — a deadlock regression guard for the orchestration layer.
    """

    def fake_poster(
        *, api_base, api_key, model, prompt, seed, max_tokens, timeout_s, reasoning_effort="low"
    ):
        time.sleep(0.001)
        return ("up", {"prompt_tokens": 1.0, "completion_tokens": 1.0, "total_tokens": 2.0})

    infer = make_openrouter_infer_fn(poster=fake_poster, concurrency=4, max_retries=0)
    predictor = make_prompt_row_predictor(infer)
    df = _frame()
    res = self_improve_loop(
        df,
        make_grid_proposer([Variant(id="c1"), Variant(id="c2")]),
        predictor,
        Variant(id="base"),
        seeds=(0, 1),
        noise_band=0.05,
        dry_rounds=2,
        max_trials=3,
    )
    # completion is the assertion — a deadlock would hang the test, not fail it
    assert res.stopped_reason in {"converged", "dry", "max_trials"}
    assert len(res.records) >= 1
