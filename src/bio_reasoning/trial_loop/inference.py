"""OpenRouter gpt-oss-120b inference for the trial-loop DE votes signal.

Builds an :data:`~bio_reasoning.trial_loop.loop.InferFn` — ``(prompts, seed) ->
one raw text per prompt`` — backed by the OpenAI-compatible chat endpoint
(:func:`post_chat_completion`). The trial-loop's ``predict_variant`` calls this
once per seed in ``variant.seeds`` and averages the parsed up/down calls into
graded vote-fraction scores: that per-seed averaging *is* text self-consistency,
so no separate votes aggregator is needed. Diversity across samples comes from
``temperature`` (gpt-oss defaults to 1.0), varied by seed.

Backend = OpenRouter (``https://openrouter.ai/api/v1``) serving
``openai/gpt-oss-120b`` — the real competition model, so no proxy/transfer risk.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor

from bio_reasoning.utils.openai_compat import post_chat_completion

_DEFAULT_BASE = "https://openrouter.ai/api/v1"
_DEFAULT_MODEL = "openai/gpt-oss-120b"


def make_openrouter_infer_fn(
    *,
    api_base: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    max_tokens: int = 512,
    reasoning_effort: str = "low",
    timeout_s: int = 120,
    concurrency: int = 8,
    poster=post_chat_completion,
):
    """Return an ``InferFn`` that calls gpt-oss over an OpenAI-compatible endpoint.

    Env fallbacks (resolved once, at build time):
      * ``api_base`` ← ``BIOREASONING_OPENAI_API_BASE`` (default OpenRouter).
      * ``api_key``  ← ``BIOREASONING_OPENAI_API_KEY`` / ``OPENAI_API_KEY``.
      * ``model``    ← ``BIOREASONING_OPENAI_MODEL`` (default ``openai/gpt-oss-120b``).

    ``max_tokens`` is deliberately generous: gpt-oss-120b is a reasoning model that
    emits harmony/reasoning tokens before the answer (a tight cap returns empty
    content). Empty replies fall through to ``parse_answer``'s neutral default.

    The returned callable carries a mutable ``token_totals`` dict (prompt /
    completion / total) accumulated across all calls — the budget hook Goal 4 reads.
    ``poster`` is injectable so the wiring is unit-testable without network.
    """
    api_base = api_base or os.getenv("BIOREASONING_OPENAI_API_BASE") or _DEFAULT_BASE
    api_key = api_key or os.getenv("BIOREASONING_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    model = model or os.getenv("BIOREASONING_OPENAI_MODEL") or _DEFAULT_MODEL

    token_totals = {"prompt_tokens": 0.0, "completion_tokens": 0.0, "total_tokens": 0.0}

    def _one(prompt: str, seed: int) -> str:
        text, stats = poster(
            api_base=api_base,
            api_key=api_key,
            model=model,
            prompt=prompt,
            seed=seed,
            max_tokens=max_tokens,
            timeout_s=timeout_s,
            reasoning_effort=reasoning_effort,
        )
        for k in token_totals:
            token_totals[k] += float(stats.get(k, 0.0))
        return text

    def _infer(prompts: Sequence[str], seed: int) -> list[str]:
        if concurrency <= 1:
            return [_one(p, seed) for p in prompts]
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            return list(ex.map(lambda p: _one(p, seed), prompts))

    _infer.token_totals = token_totals  # type: ignore[attr-defined]
    return _infer
