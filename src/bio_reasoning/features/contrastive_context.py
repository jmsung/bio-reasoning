"""CORE-style contrastive evidence: related perturbations' KNOWN outcomes.

For a query ``(pert, gene)``, retrieve neighbour train rows (same neighbour graph as
:mod:`~bio_reasoning.features.neighbor_retrieval`) and organize them as **positive**
(differentially expressed: up/down) vs **negative** (none) reference examples — the
contrastive set a CORE scorer classifies *against*, instead of scoring the pair in
isolation (Yuan 2026, "Plausibility Is Not Prediction").

Leak-free: train-only, excludes the query's own pair. See
``findings/contrastive-de-core-assessment.md`` for why this is a *gated kill-test* —
CORE-Voting over this set is our neighbour-retrieval-DE, already ~0.498 on dual-OOD.
"""

from __future__ import annotations

import pandas as pd

Reference = tuple[str, str, str]  # (pert, gene, label)


def contrastive_references(
    pert: str,
    gene: str,
    train_df: pd.DataFrame,
    pert_neighbors: dict[str, set[str]],
    gene_neighbors: dict[str, set[str]],
    min_support: int = 3,
) -> dict[str, list[Reference]]:
    """Return ``{'positive': [...], 'negative': [...]}`` of neighbour train references.

    Positives are DE (``up``/``down``), negatives are ``none`` — the contrastive
    evidence for the query. Neighbour = a train row whose ``pert`` is in
    ``pert_neighbors[pert]`` OR whose ``gene`` is in ``gene_neighbors[gene]``, minus
    the query's own pair (leak-free). Both lists empty when fewer than ``min_support``
    neighbours are retrieved (evidence too thin).
    """
    pn = pert_neighbors.get(pert, set())
    gn = gene_neighbors.get(gene, set())
    mask = train_df["pert"].isin(pn) | train_df["gene"].isin(gn)
    mask &= ~((train_df["pert"] == pert) & (train_df["gene"] == gene))
    hits = train_df.loc[mask, ["pert", "gene", "label"]]
    if len(hits) < min_support:
        return {"positive": [], "negative": []}

    is_de = hits["label"] != "none"
    return {
        "positive": [(r.pert, r.gene, r.label) for r in hits[is_de].itertuples(index=False)],
        "negative": [(r.pert, r.gene, r.label) for r in hits[~is_de].itertuples(index=False)],
    }
