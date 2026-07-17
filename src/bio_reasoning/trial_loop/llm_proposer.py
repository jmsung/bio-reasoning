"""LLM-as-optimizer proposer — gpt-oss reads the reward history and proposes a config.

An alternative to UCB: instead of a fixed exploration rule, prompt the model with
``reflect(history)`` (per-variant reward summary) and let it emit the next config to
try as JSON. Same ``Proposer`` seam. Every proposal is **validated** — malformed
output, an unknown retrieval mode, a bad sample count, or a config whose id names a
KB-ruled-out static channel all **fall back to the ``fallback`` proposer** (the
bandit), so a hallucinated or dead suggestion can never derail the loop.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable

from bio_reasoning.trial_loop.reflect import Proposer
from bio_reasoning.trial_loop.ruled_out import is_ruled_out
from bio_reasoning.trial_loop.types import Variant

_SAMPLE_SEEDS: dict[int, tuple[int, ...]] = {3: (42, 43, 44), 5: (42, 43, 44, 45, 46)}
_RETRIEVALS = ("random", "go_category")
_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)

# propose_fn(reflection) -> raw model text proposing the next config.
ProposeFn = Callable[[str], str]


def _parse_variant(raw: str) -> Variant | None:
    """Extract a config JSON from ``raw`` and validate it into a Variant, else None."""
    m = _JSON_RE.search(raw or "")
    if not m:
        return None
    try:
        cfg = json.loads(m.group(0))
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(cfg, dict):
        return None
    retrieval = cfg.get("retrieval")
    n_samples = cfg.get("n_samples")
    n_few_shot = cfg.get("n_few_shot")
    if retrieval not in _RETRIEVALS or n_samples not in _SAMPLE_SEEDS:
        return None
    if not isinstance(n_few_shot, int) or n_few_shot < 0:
        return None
    approach = str(cfg.get("approach", "")).strip()
    tag = f"{approach}-" if approach else ""
    vid = f"llm-{tag}nfs{n_few_shot}-{retrieval}-s{n_samples}"
    if is_ruled_out(vid):  # LLM wandered into a dead static channel → reject
        return None
    return Variant(
        id=vid, n_few_shot=n_few_shot, retrieval=retrieval, seeds=_SAMPLE_SEEDS[n_samples]
    )


def make_llm_proposer(propose_fn: ProposeFn, fallback: Proposer) -> Proposer:
    """Proposer that asks ``propose_fn`` for the next config, falling back on any failure.

    ``propose_fn(reflection) -> raw text``; for leaderboard use wrap the OpenRouter
    gpt-oss caller. A valid, live proposal is returned as a Variant; anything else
    (unparseable / invalid / ruled-out) delegates to ``fallback`` (typically the bandit).
    """

    def _propose(reflection: str, history: list) -> Variant | None:
        variant = _parse_variant(propose_fn(reflection))
        if variant is None:
            return fallback(reflection, history)
        return variant

    return _propose
