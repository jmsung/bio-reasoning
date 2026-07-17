"""Real-data agent tools for the Track B agentic predictor (offline-first).

Wraps the cached ``src`` feature loaders as functional agent tools: GO:BP terms
(:func:`~bio_reasoning.features.gene_function.load_go_terms`), STRING interaction
partners (:func:`~bio_reasoning.features.string_graph.fetch_string_partners`), and
Traxler native-macrophage direction (:mod:`bio_reasoning.data.traxler_labels`).
Every tool returns a *grounded* natural-language string from real gene knowledge
— not a stub — and is deterministic given a warm cache, so the loop is offline-
testable (the open Track B lane is genuinely functional tools, not cosmetic
scaffolding — ``findings/competitor-landscape.md``).

A :class:`ToolBackend` injects the three data sources, so the same tool functions
run against real caches in the CLI and against fakes in tests. :func:`make_tools`
assembles the DSPy-compatible callables; ``include_traxler=False`` drops the
Traxler-direction tool — used when the Traxler fold is the eval, so the tool can
never serve the very labels it is validated against (``findings/direction-
transfers-de-doesnt.md``: Traxler is a validation substrate).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from bio_reasoning.features.gene_function import load_go_terms
from bio_reasoning.features.string_graph import fetch_string_partners

# Data-source seams the tools query (all offline once caches are warm).
GoTermsFn = Callable[[str], "list[str]"]
StringPartnersFn = Callable[[str], "list[str]"]
# (pert, gene) -> "up"/"down"/"none", or None when the pair is uncovered.
TraxlerDirectionFn = Callable[[str, str], "str | None"]

_TRAXLER_PHRASE = {
    "up": "up-regulated",
    "down": "down-regulated",
    "none": "not differentially expressed",
}


@dataclass(frozen=True)
class ToolBackend:
    """The real-data sources the agent tools read (injected for testability)."""

    go_terms: GoTermsFn
    string_partners: StringPartnersFn
    traxler_direction: TraxlerDirectionFn


def format_go_terms(gene: str, terms: list[str], limit: int = 12) -> str:
    if not terms:
        return f"No GO:BP terms found for '{gene}' (mouse)."
    shown = terms[:limit]
    return f"GO:BP terms for {gene} ({len(shown)} of {len(terms)}): " + "; ".join(shown)


def format_string_partners(gene: str, partners: list[str], limit: int = 15) -> str:
    if not partners:
        return f"No STRING interaction partners found for '{gene}' (mouse)."
    shown = list(partners)[:limit]
    return (
        f"STRING interaction partners for {gene} (mouse, {len(shown)} of {len(partners)}): "
        + ", ".join(shown)
    )


def format_traxler_direction(pert: str, gene: str, direction: str | None) -> str:
    if direction is None:
        return f"No Traxler native measurement for perturbation '{pert}' -> gene '{gene}'."
    phrase = _TRAXLER_PHRASE.get(direction, direction)
    return (
        f"Traxler native-macrophage measurement: knocking down '{pert}' leaves "
        f"'{gene}' {phrase}."
    )


def make_tools(backend: ToolBackend, include_traxler: bool = True) -> list[Callable[..., str]]:
    """Assemble the DSPy-compatible tool callables over ``backend``.

    ``include_traxler=False`` omits the Traxler-direction tool so it cannot leak the
    labels of the Traxler validation fold (use it only for the dual-OOD reward).
    """

    def go_terms(gene: str) -> str:
        """Look up the Gene Ontology biological-process (GO:BP) terms for a mouse
        gene. Use this to learn what biological processes/pathways a gene is
        involved in before predicting its regulation."""
        return format_go_terms(gene, backend.go_terms(gene))

    def string_partners(gene: str) -> str:
        """Look up known protein interaction partners for a mouse gene from the
        STRING database. Use this to find network neighbours that may co-regulate
        the target."""
        return format_string_partners(gene, backend.string_partners(gene))

    tools: list[Callable[..., str]] = [go_terms, string_partners]

    if include_traxler:

        def traxler_direction(pert: str, gene: str) -> str:
            """Look up the measured native-macrophage direction (up/down/none) of a
            target gene after knocking down a perturbation gene, from the Traxler KO
            screen -- independent real evidence in the challenge's exact cell type."""
            return format_traxler_direction(pert, gene, backend.traxler_direction(pert, gene))

        tools.append(traxler_direction)

    return tools


def traxler_direction_lookup(labels_df: pd.DataFrame) -> TraxlerDirectionFn:
    """Build a ``(pert, gene) -> label`` lookup from a Traxler labels frame.

    ``labels_df`` has columns ``[pert, gene, label]`` (see
    :func:`bio_reasoning.data.traxler_labels.logfc_to_labels`). Uncovered pairs
    return ``None``.
    """
    idx = {(str(r["pert"]), str(r["gene"])): str(r["label"]) for r in labels_df.to_dict("records")}
    return lambda pert, gene: idx.get((pert, gene))


def make_cache_backend(
    go_cache: str | Path,
    string_cache: str | Path,
    traxler_direction: TraxlerDirectionFn | None = None,
) -> ToolBackend:
    """Build a :class:`ToolBackend` over the on-disk GO / STRING caches.

    Cache-hits are offline; a miss falls through to the loader's fetch. Pass
    ``traxler_direction`` (from :func:`traxler_direction_lookup`) to enable the
    Traxler tool, or leave it ``None`` (every pair uncovered) when the Traxler fold
    is the eval.
    """

    def go(gene: str) -> list[str]:
        return load_go_terms([gene], go_cache).get(gene, [])

    def partners(gene: str) -> list[str]:
        return sorted(fetch_string_partners([gene], string_cache).get(gene, set()))

    trax: TraxlerDirectionFn = traxler_direction or (lambda pert, gene: None)
    return ToolBackend(go_terms=go, string_partners=partners, traxler_direction=trax)
