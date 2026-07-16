"""SUMMER-style neighbor-retrieval DE channel.

For an unseen ``(pert, gene)`` pair, borrow the *measured labels* of TRAIN rows
whose pert is a neighbor of the query pert OR whose gene is a neighbor of the
query gene (neighbours from a STRING/GO graph), and aggregate them into the two
buses the Track A metric decomposes into:

- ``s_de`` = fraction of retrieved neighbour rows that are differentially expressed
- ``r``    = P(up | DE) among the retrieved DE rows

Works under the dual-OOD split by construction: the query pair itself is never in
train, but a *neighbour* of its pert or gene can be — that is the only "seen"
requirement. Retrieval is TRAIN-only and always excludes the query's own pair, so
it cannot read a val row's own label.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bio_reasoning.models.fuse import Channel


def retrieve_neighbor_labels(
    pert: str,
    gene: str,
    train_df: pd.DataFrame,
    pert_neighbors: dict[str, set[str]],
    gene_neighbors: dict[str, set[str]],
    min_support: int = 1,
) -> tuple[float, float]:
    """Return ``(s_de, r)`` borrowed from neighbour train rows, or ``(nan, nan)``.

    Retrieves train rows whose ``pert`` is in ``pert_neighbors[pert]`` OR whose
    ``gene`` is in ``gene_neighbors[gene]``, excluding the query's own pair. With
    fewer than ``min_support`` retrieved rows the evidence is too thin → ``nan``
    (uncovered). ``r`` defaults to ``0.5`` when retrieved rows carry no DE row.
    """
    pn = pert_neighbors.get(pert, set())
    gn = gene_neighbors.get(gene, set())
    mask = train_df["pert"].isin(pn) | train_df["gene"].isin(gn)
    mask &= ~((train_df["pert"] == pert) & (train_df["gene"] == gene))
    labels = train_df.loc[mask, "label"].to_numpy()
    if len(labels) < min_support:
        return float("nan"), float("nan")
    s_de = float((labels != "none").mean())
    de = labels[labels != "none"]
    r = float((de == "up").mean()) if len(de) else 0.5
    return s_de, r


def neighbor_channel(
    queries: pd.DataFrame,
    train_df: pd.DataFrame,
    pert_neighbors: dict[str, set[str]],
    gene_neighbors: dict[str, set[str]],
    min_support: int = 1,
) -> Channel:
    """Build a :class:`~bio_reasoning.models.fuse.Channel` over ``queries`` rows.

    ``queries`` has ``pert``/``gene`` columns aligned to the rows being scored;
    uncovered rows carry ``NaN`` so ``fuse`` falls back to the other channels.
    """
    s_de = np.empty(len(queries))
    r = np.empty(len(queries))
    for i, (p, g) in enumerate(zip(queries["pert"], queries["gene"], strict=True)):
        s_de[i], r[i] = retrieve_neighbor_labels(
            p, g, train_df, pert_neighbors, gene_neighbors, min_support
        )
    return Channel(name="neighbor_retrieval", s_de=s_de, r=r)
