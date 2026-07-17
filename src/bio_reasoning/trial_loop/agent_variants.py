"""The agentic tool-config variant space + a denylist-aware proposer.

Loop style ③: instead of Track A prompt knobs (``de_variants``), the agentic lane
searches **tool configs** — which real-data tools (``trial_loop.tools``) the agent
may call — crossed with the self-consistency sample count. Retrieval few-shot is
*inert* for a tool-agent (``make_agent_row_predictor`` gathers evidence via tools,
not exemplars), so it is deliberately omitted here rather than carried as a dead
knob. ``make_agent_proposer`` filters KB-ruled-out channels ([[ruled_out]]) exactly
as the DE proposer does.
"""

from __future__ import annotations

from collections.abc import Sequence

from bio_reasoning.trial_loop.reflect import Proposer, make_grid_proposer
from bio_reasoning.trial_loop.ruled_out import is_ruled_out
from bio_reasoning.trial_loop.types import Variant


def _seeds(n: int) -> tuple[int, ...]:
    """The seed tuple ``predict_variant`` averages over for ``n`` self-consistency
    samples. The DSPy agent is unseeded (temperature 1.0), so ``n`` samples are ``n``
    repeated runs averaged into a graded score; ``n == 1`` is a single call."""
    return tuple(42 + i for i in range(n))


# Canonical real-data tool subsets (keys are stable id fragments for the archive).
# Each subset is genuinely functional gene knowledge (findings/competitor-landscape.md);
# "prior" is the tool-free baseline the agentic configs must beat.
AGENT_TOOL_SUBSETS: dict[str, tuple[str, ...]] = {
    "prior": (),
    "go": ("go_terms",),
    "net": ("string_partners",),
    "go-net": ("go_terms", "string_partners"),
    "go-net-trax": ("go_terms", "string_partners", "traxler_direction"),
}


def agent_variant_grid(
    subsets: dict[str, tuple[str, ...]] | None = None,
    sample_counts: Sequence[int] = (1, 3),
    include_traxler: bool = True,
    self_critique: Sequence[bool] = (False,),
) -> list[Variant]:
    """Enumerate agentic tool-config variants (all id-prefixed ``agent-``).

    Each variant fixes a tool subset, a self-consistency sample count (its ``seeds``
    length), and whether the agent runs a self-critique pass (id suffix ``-crit``).
    ``self_critique`` defaults to off-only so the grid stays lean; pass
    ``(False, True)`` to A/B the critique. ``include_traxler=False`` drops every
    subset naming ``traxler_direction`` — used when the Traxler fold is the eval, so
    the tool can never leak the labels it is validated against.
    """
    subsets = subsets or AGENT_TOOL_SUBSETS
    grid: list[Variant] = []
    for name, tools in subsets.items():
        if not include_traxler and "traxler_direction" in tools:
            continue
        for nc in sample_counts:
            for crit in self_critique:
                vid = f"agent-{name}-s{nc}" + ("-crit" if crit else "")
                grid.append(Variant(id=vid, tools=tools, seeds=_seeds(nc), self_critique=crit))
    return grid


def make_agent_proposer(candidates: list[Variant] | None = None) -> Proposer:
    """Grid proposer over the agentic variants, with ruled-out channels filtered out.

    ``candidates`` defaults to :func:`agent_variant_grid`. Any candidate whose id
    names a KB-ruled-out channel is dropped before the walk.
    """
    if candidates is None:
        candidates = agent_variant_grid()
    live = [v for v in candidates if not is_ruled_out(v.id)]
    return make_grid_proposer(live)
