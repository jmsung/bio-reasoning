"""DepMap co-essentiality neighbour key for the label-borrowing direction channel.

The direction lever is a property of the neighbour *key*, not the borrowing mechanism
(knowledge/wiki/findings/neighbor-retrieval-direction-lever.md): labeled-pair graph
neighbours that put co-regulated genes next to each other carry direction; naming-family
keys don't. STRING is one such key (physical/annotation interaction). Co-essentiality is
another, potentially *stronger* one: genes whose CRISPR knockout fitness effects correlate
across DepMap's ~1100 cell lines are in the same functional module / complex, so they are
co-regulated in a way physical-interaction edges only partially capture.

We build the neighbour graph from ``CRISPRGeneEffect.csv`` (cell line × gene effect matrix,
DepMap Public 23Q4, figshare file 43346616, ~400 MB): for each universe gene, its top-k
most positively-correlated genes are its co-essential partners. DepMap is human; the mouse
BMDM universe maps by uppercasing the symbol (``Abi1`` → ``ABI1``), and partners map back
to the mouse universe symbol so the graph is a drop-in for ``neighbor_channel``.
"""

from __future__ import annotations

import json
import os

import pandas as pd

# DepMap Public 23Q4 CRISPRGeneEffect.csv (cell line × gene knockout effect), figshare mirror.
GENE_EFFECT_URL = "https://ndownloader.figshare.com/files/43346616"


def parse_effect_columns(columns: list[str]) -> dict[str, str]:
    """Map ``UPPER(symbol) -> original column`` for a gene-effect header.

    Columns look like ``"Actb (11461)"``; the leading ``Unnamed: 0`` (cell-line id) and
    any column without a symbol are skipped. On a rare uppercase collision the first wins.
    """
    out: dict[str, str] = {}
    for col in columns:
        if col.startswith("Unnamed"):
            continue
        sym = col.split(" (")[0].strip().upper()
        if sym and sym not in out:
            out[sym] = col
    return out


def coessential_partners(
    corr: pd.DataFrame, top_k: int = 25, min_corr: float = 0.2
) -> dict[str, list[str]]:
    """Top-k co-essential partners per gene from a correlation matrix (index=cols=symbols).

    Co-essentiality is a functional-similarity graph, so only **positive** correlations
    above ``min_corr`` count; each gene's partners are its strongest such neighbours
    (self excluded), highest correlation first, capped at ``top_k``.
    """
    out: dict[str, list[str]] = {}
    genes = list(corr.index)
    for g in genes:
        s = corr[g].drop(labels=[g], errors="ignore")
        s = s[s >= min_corr].dropna()
        out[g] = list(s.sort_values(ascending=False).index[:top_k])
    return out


def map_partners_to_universe(
    upper_partners: dict[str, list[str]], upper2mouse: dict[str, str]
) -> dict[str, list[str]]:
    """Re-key an uppercase partner graph to the mouse universe symbols, dropping off-universe.

    ``upper2mouse`` maps ``UPPER(symbol) -> mouse symbol`` for the universe; any partner
    not in the universe (or query gene not in it) is dropped so the graph only references
    symbols the train set can carry.
    """
    out: dict[str, list[str]] = {}
    for u, partners in upper_partners.items():
        if u not in upper2mouse:
            continue
        mapped = [upper2mouse[p] for p in partners if p in upper2mouse]
        out[upper2mouse[u]] = mapped
    return out


def build_coessentiality_partners(
    gene_effect_csv: str,
    universe: list[str],
    *,
    top_k: int = 25,
    min_corr: float = 0.2,
    min_periods: int = 50,
) -> dict[str, list[str]]:
    """Co-essentiality neighbour graph over ``universe`` mouse symbols (drop-in for STRING).

    Loads only the universe columns of the gene-effect matrix, Pearson-correlates the
    dependency profiles pairwise (``min_periods`` co-screened cell lines required), and
    returns ``mouse symbol -> [mouse co-essential partners]``. Coverage is limited to
    universe genes present in DepMap (mouse→human uppercase ortholog match).
    """
    header = pd.read_csv(gene_effect_csv, nrows=0).columns.tolist()
    upper2col = parse_effect_columns(header)

    upper2mouse: dict[str, str] = {}
    for m in universe:
        upper2mouse.setdefault(str(m).upper(), str(m))

    present = [u for u in upper2mouse if u in upper2col]
    usecols = [header[0]] + [upper2col[u] for u in present]
    mat = pd.read_csv(gene_effect_csv, usecols=usecols, index_col=0)
    mat.columns = [c.split(" (")[0].strip().upper() for c in mat.columns]

    corr = mat.corr(min_periods=min_periods)
    upper_partners = coessential_partners(corr, top_k=top_k, min_corr=min_corr)
    return map_partners_to_universe(upper_partners, upper2mouse)


def load_coessentiality_partners(
    universe: list[str],
    cache_path: str,
    gene_effect_csv: str,
    **kwargs,
) -> dict[str, set[str]]:
    """Cached co-essentiality partner graph (``symbol -> set(partners)``) for ``universe``.

    Cached as JSON (sorted lists) at ``cache_path`` on first call; offline thereafter.
    Returns sets to match ``fetch_string_partners`` / ``neighbor_channel``'s expectation.
    """
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return {k: set(v) for k, v in json.load(f).items()}
    partners = build_coessentiality_partners(gene_effect_csv, universe, **kwargs)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump({k: sorted(v) for k, v in partners.items()}, f)
    return {k: set(v) for k, v in partners.items()}


__all__ = [
    "parse_effect_columns",
    "coessential_partners",
    "map_partners_to_universe",
    "build_coessentiality_partners",
    "load_coessentiality_partners",
]
