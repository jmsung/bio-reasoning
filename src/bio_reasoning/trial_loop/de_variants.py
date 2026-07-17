"""The live DE-votes variant space + a denylist-aware proposer.

The loop searches the one lane the KB hasn't ruled out: the gpt-oss votes/text
self-consistency signal. This grid varies the knobs that plausibly move that signal
— few-shot count, exemplar retrieval, and the number of self-consistency samples
(``variant.seeds`` length). ``make_de_proposer`` filters the KB-ruled-out static
channels ([[ruled_out]]) so the loop can never burn budget on a dead basin.
"""

from __future__ import annotations

from collections.abc import Sequence

from bio_reasoning.trial_loop.reflect import Proposer, make_grid_proposer
from bio_reasoning.trial_loop.ruled_out import is_ruled_out
from bio_reasoning.trial_loop.types import Variant

# self-consistency sample count -> the seed tuple predict_variant averages over.
_SAMPLE_SEEDS: dict[int, tuple[int, ...]] = {
    3: (42, 43, 44),
    5: (42, 43, 44, 45, 46),
}


def de_variant_grid(
    few_shots: Sequence[int] = (0, 2, 4),
    retrievals: Sequence[str] = ("random", "go_category"),
    sample_counts: Sequence[int] = (3, 5),
) -> list[Variant]:
    """Enumerate the live votes/self-consistency variants (all id-prefixed ``de-votes-``).

    Retrieval is only meaningful with few-shot exemplars, so ``few_shots == 0`` collapses
    to a single retrieval-free variant. Each variant's ``seeds`` sets the self-consistency
    sample count.
    """
    grid: list[Variant] = []
    seen: set[str] = set()
    for nfs in few_shots:
        rets = ("random",) if nfs == 0 else tuple(retrievals)
        for ret in rets:
            for nc in sample_counts:
                vid = f"de-votes-nfs{nfs}" + (f"-{ret}" if nfs > 0 else "") + f"-s{nc}"
                if vid in seen:
                    continue
                seen.add(vid)
                grid.append(Variant(id=vid, n_few_shot=nfs, retrieval=ret, seeds=_SAMPLE_SEEDS[nc]))
    return grid


def make_de_proposer(candidates: list[Variant] | None = None) -> Proposer:
    """Grid proposer over the live DE variants, with ruled-out channels filtered out.

    ``candidates`` defaults to :func:`de_variant_grid`. Any candidate whose id names a
    KB-ruled-out static channel is dropped before the walk — the loop cannot propose it.
    """
    if candidates is None:
        candidates = de_variant_grid()
    live = [v for v in candidates if not is_ruled_out(v.id)]
    return make_grid_proposer(live)
