"""Proposer selection — the runner's ``--proposer {grid,bandit,llm}`` switch.

One place that maps a name to a :data:`Proposer` over the live DE-votes variant
space, so the runner (and any A/B harness) picks a search policy without knowing
each proposer's construction. ``llm`` uses the LLM-as-optimizer with the bandit as
its fallback, so a hallucinated proposal degrades to a principled policy.
"""

from __future__ import annotations

from collections.abc import Callable

from bio_reasoning.trial_loop.bandit import make_bandit_proposer
from bio_reasoning.trial_loop.de_variants import de_variant_grid, make_de_proposer
from bio_reasoning.trial_loop.llm_proposer import make_llm_proposer
from bio_reasoning.trial_loop.reflect import Proposer
from bio_reasoning.trial_loop.types import Variant

PROPOSERS = ("grid", "bandit", "llm")


def select_proposer(
    name: str,
    candidates: list[Variant] | None = None,
    propose_fn: Callable[[str], str] | None = None,
) -> Proposer:
    """Return a proposer over ``candidates`` (default :func:`de_variant_grid`).

    - ``grid``  — fixed walk, each variant once (``make_de_proposer``).
    - ``bandit`` — UCB1 resampling by observed reward (``make_bandit_proposer``).
    - ``llm``   — LLM-as-optimizer (``make_llm_proposer``), falling back to the bandit;
      requires ``propose_fn``.
    """
    arms = candidates if candidates is not None else de_variant_grid()
    if name == "grid":
        return make_de_proposer(arms)
    if name == "bandit":
        return make_bandit_proposer(arms)
    if name == "llm":
        if propose_fn is None:
            raise ValueError("proposer 'llm' requires propose_fn")
        return make_llm_proposer(propose_fn, fallback=make_bandit_proposer(arms))
    raise ValueError(f"unknown proposer: {name!r} (choose from {PROPOSERS})")
