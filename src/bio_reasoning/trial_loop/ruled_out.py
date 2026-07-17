"""KB-ruled-out DE channels — the denylist the loop must never re-explore.

Static/knowledge DE channels are a locked basin: ~7 independent attacks all landed
at chance (AUROC_de ≈ 0.50). The loop's only live lane is the LLM votes signal, so
any variant encoding a ruled-out static channel is wasted budget. Each key is cited
to the finding that killed it; add a line (with cite) when a new finding rules one
out. Matched as a case-insensitive substring of a variant id.
"""

from __future__ import annotations

RULED_OUT: frozenset[str] = frozenset(
    {
        # findings/marginal-de-caps-at-degree.md — STRING degree caps DE ~0.536
        "string-degree",
        "marginal-degree",
        "marginal-de",
        # findings/curated-edges-fail-de-axis.md — CollecTRI / STRING hops at chance
        "collectri",
        "string-1hop",
        "string-2hop",
        "curated-edge",
        # findings/neighbor-retrieval-direction-lever.md — retrieval-DE = 0.498 (DIR-only lever)
        "neighbour-retrieval-de",
        "neighbor-retrieval-de",
        "retrieval-de",
        # feat/family-retrieval-baseline (PR #29) — family retrieval DE 0.502
        "family-retrieval",
        # findings/contrastive-de-core-assessment.md — CORE-Voting DE 0.498
        "contrastive-de",
        "core-voting",
        # feat/richer-marginal-de (PR #49) — DepMap essentiality adds nothing over degree
        "essentiality-de",
        "depmap-de",
    }
)


def is_ruled_out(variant_id: str) -> bool:
    """True if ``variant_id`` names a KB-ruled-out static DE channel."""
    vid = variant_id.lower()
    return any(key in vid for key in RULED_OUT)
