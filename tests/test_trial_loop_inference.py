"""Offline tests for the OpenRouter gpt-oss infer_fn (injected poster, no network)."""

from __future__ import annotations

from bio_reasoning.trial_loop.inference import make_openrouter_infer_fn
from bio_reasoning.trial_loop.loop import make_prompt_row_predictor
from bio_reasoning.trial_loop.types import Variant


def _fake_poster(replies: dict[str, str]):
    """Poster stub: map prompt -> canned text; record every call's kwargs."""
    calls: list[dict] = []

    def _poster(*, api_base, api_key, model, prompt, seed, max_tokens, timeout_s, reasoning_effort):
        calls.append(
            {
                "api_base": api_base,
                "api_key": api_key,
                "model": model,
                "prompt": prompt,
                "seed": seed,
                "max_tokens": max_tokens,
                "timeout_s": timeout_s,
                "reasoning_effort": reasoning_effort,
            }
        )
        text = replies.get(prompt, "C) does not significantly affect")
        return text, {"prompt_tokens": 3.0, "completion_tokens": 5.0, "total_tokens": 8.0}

    return _poster, calls


def test_infer_fn_returns_one_text_per_prompt_in_order():
    poster, _ = _fake_poster({"p0": "A) upregulation", "p1": "B) down-regulation"})
    infer = make_openrouter_infer_fn(
        api_base="http://x/v1",
        api_key="k",
        model="openai/gpt-oss-120b",
        concurrency=4,
        poster=poster,
    )
    out = infer(["p0", "p1", "p2"], seed=42)
    assert out == ["A) upregulation", "B) down-regulation", "C) does not significantly affect"]


def test_infer_fn_forwards_params_and_seed():
    poster, calls = _fake_poster({})
    infer = make_openrouter_infer_fn(
        api_base="http://x/v1",
        api_key="secret",
        model="m",
        max_tokens=777,
        timeout_s=99,
        reasoning_effort="medium",
        concurrency=1,
        poster=poster,
    )
    infer(["only"], seed=7)
    c = calls[0]
    assert c["api_key"] == "secret" and c["model"] == "m" and c["max_tokens"] == 777
    assert c["seed"] == 7 and c["timeout_s"] == 99 and c["reasoning_effort"] == "medium"


def test_infer_fn_accumulates_token_totals():
    poster, _ = _fake_poster({})
    infer = make_openrouter_infer_fn(
        api_base="b", api_key="k", model="m", concurrency=2, poster=poster
    )
    infer(["a", "b", "c"], seed=0)
    assert infer.token_totals["total_tokens"] == 24.0  # 3 calls * 8


def test_wires_into_prompt_row_predictor_and_parses():
    # votes/text self-consistency: parse_answer maps texts -> discrete (up, down)
    poster, _ = _fake_poster({"P-up": "A) upregulation", "P-down": "B) down-regulation"})
    infer = make_openrouter_infer_fn(api_base="b", api_key="k", model="m", poster=poster)
    predict = make_prompt_row_predictor(infer)
    variant = Variant(id="t", prompt_template="{pert}")  # template -> prompt == pert value
    rows = [
        {"pert": "P-up", "gene": "g"},
        {"pert": "P-down", "gene": "g"},
        {"pert": "P-x", "gene": "g"},
    ]
    preds = predict(rows, variant, 0, lambda r: None)
    assert preds == [(1.0, 0.0), (0.0, 1.0), (0.0, 0.0)]
