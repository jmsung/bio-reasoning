"""Char/prefix family-retrieval DE+direction channel.

A cheap, identity-free sibling of :mod:`bio_reasoning.features.neighbor_retrieval`:
instead of a STRING/GO graph, the retrieval key is the symbol's **family** — the
symbol with its trailing numeric index stripped and case-folded (``Rpl13`` →
``rpl``, ``Ifit3`` → ``ifit``). Gene families share this prefix, so an unseen
``(pert, gene)`` pair can borrow the measured labels of TRAIN rows in the same
gene- or pert-family and aggregate them into the two Track A buses:

- ``s_de`` = fraction of borrowed rows that are differentially expressed
- ``r``    = P(up | DE) among the borrowed DE rows

Leak-free by construction: on the dual-OOD split a val pair's identity is disjoint
from train, so every borrowed row is a genuine train row; an explicit
exclude-own-pair guard additionally prevents a row from ever reading its own label.
Uncovered rows (no family peer) carry ``NaN`` so :func:`fuse` falls back to other
channels and :func:`cfa_gate` measures the real coverage.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from bio_reasoning.models.fuse import Channel

_TRAILING_INDEX = re.compile(r"\d+$")


def family_key(symbol: str) -> str:
    """Return the family key: ``symbol`` minus its trailing numeric index, lowered.

    ``Rpl13`` → ``rpl``, ``Ifit3`` → ``ifit``, ``Actb`` → ``actb``. The trailing
    index is the within-family numbering, so stripping it groups a family together.
    """
    return _TRAILING_INDEX.sub("", str(symbol)).lower()


def retrieve_family_labels(
    pert: str,
    gene: str,
    train_df: pd.DataFrame,
    *,
    use_pert: bool = True,
    use_gene: bool = True,
    min_support: int = 1,
) -> tuple[float, float]:
    """Return ``(s_de, r)`` borrowed from same-family train rows, or ``(nan, nan)``.

    Retrieves train rows whose pert-family matches the query's (when ``use_pert``)
    OR whose gene-family matches (when ``use_gene``), excluding the query's own
    exact ``(pert, gene)`` pair. With fewer than ``min_support`` borrowed rows the
    evidence is too thin → ``nan`` (uncovered). ``r`` defaults to ``0.5`` when the
    borrowed rows carry no DE row.
    """
    pk = _family_col(train_df, "pert")
    gk = _family_col(train_df, "gene")
    mask = pd.Series(False, index=train_df.index)
    if use_pert:
        mask = mask | (pk == family_key(pert))
    if use_gene:
        mask = mask | (gk == family_key(gene))
    mask = mask & ~((train_df["pert"] == pert) & (train_df["gene"] == gene))

    labels = train_df.loc[mask, "label"].to_numpy()
    if len(labels) < min_support:
        return float("nan"), float("nan")
    s_de = float((labels != "none").mean())
    de = labels[labels != "none"]
    r = float((de == "up").mean()) if len(de) else 0.5
    return s_de, r


def _family_col(df: pd.DataFrame, col: str) -> pd.Series:
    """Family keys for ``df[col]``, using a cached ``_<col>_fam`` column when present."""
    cached = f"_{col}_fam"
    if cached in df.columns:
        return df[cached]
    return df[col].map(family_key)


class FamilyRetriever:
    """Fit family keys on a train set, then score query pairs into a :class:`Channel`."""

    def __init__(self, use_pert: bool = True, use_gene: bool = True, min_support: int = 1):
        self.use_pert = use_pert
        self.use_gene = use_gene
        self.min_support = min_support

    def fit(self, train_df: pd.DataFrame) -> "FamilyRetriever":
        """Cache the train rows with precomputed pert/gene family-key columns."""
        tr = train_df.reset_index(drop=True).copy()
        tr["_pert_fam"] = tr["pert"].map(family_key)
        tr["_gene_fam"] = tr["gene"].map(family_key)
        self.train_ = tr
        return self

    def channel(self, queries: pd.DataFrame) -> Channel:
        """Return a ``family_retrieval`` :class:`Channel` over ``queries`` rows.

        ``queries`` has ``pert``/``gene`` columns aligned to the rows being scored;
        uncovered rows carry ``NaN``.
        """
        s_de = np.empty(len(queries))
        r = np.empty(len(queries))
        for i, (p, g) in enumerate(zip(queries["pert"], queries["gene"], strict=True)):
            s_de[i], r[i] = retrieve_family_labels(
                p,
                g,
                self.train_,
                use_pert=self.use_pert,
                use_gene=self.use_gene,
                min_support=self.min_support,
            )
        return Channel(name="family_retrieval", s_de=s_de, r=r)
