"""Traxler native pseudobulk log2FC → challenge-schema real labels.

Traxler KO150 (native mouse-macrophage CROP-seq — the challenge's exact cell type)
gives an independent, in-domain real-label fold for the self-improvement loop's gate.
A precomputed pseudobulk (per-perturbation log2FC vs untreated, offline) is thresholded
into the challenge schema ``(pert, gene, label ∈ {up, down, none})``.

Only DE presence + direction transfer from a KO screen to the challenge's CRISPRi task
— magnitude does not (see findings/direction-transfers-de-doesnt.md) — so this is a
*validation* substrate, never training labels.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

# 2-fold (|log2FC| ≥ 1.0) is the standard DE cutoff; near-zero magnitudes have noisy
# sign, and direction fidelity is exactly what this fold validates.
DEFAULT_THRESHOLD = 1.0


def logfc_to_labels(
    lookup: dict[str, dict[str, float]], threshold: float = DEFAULT_THRESHOLD
) -> pd.DataFrame:
    """Threshold a ``{pert: {gene: log2fc}}`` pseudobulk into challenge-schema labels.

    ``|log2fc| >= threshold`` → ``up``/``down`` by sign; otherwise ``none``. Returns
    a frame with columns ``[pert, gene, label, log2fc]`` (one row per pert-gene pair).
    """
    rows = []
    for pert, genes in lookup.items():
        for gene, lfc in genes.items():
            if lfc >= threshold:
                label = "up"
            elif lfc <= -threshold:
                label = "down"
            else:
                label = "none"
            rows.append((str(pert), str(gene), label, float(lfc)))
    return pd.DataFrame(rows, columns=["pert", "gene", "label", "log2fc"])


def label_distribution(df: pd.DataFrame) -> dict[str, int]:
    """Summarize a labels frame: per-class counts, DE total, and perturbation count."""
    counts = df["label"].value_counts().to_dict()
    up, down, none = counts.get("up", 0), counts.get("down", 0), counts.get("none", 0)
    return {
        "up": up,
        "down": down,
        "none": none,
        "de": up + down,
        "n_perts": int(df["pert"].nunique()),
        "n_pairs": int(len(df)),
    }


def make_traxler_exemplar_pool(
    labels_df: pd.DataFrame,
    n: int = 4,
    seed: int = 0,
    de_only: bool = True,
) -> Callable[[dict], "list[dict] | None"]:
    """Build a leak-free few-shot provider drawing real Traxler exemplars.

    Returns an ``ExamplesProvider`` (``query_row -> list[{pert, gene, label}] | None``)
    usable by a retrieval variant. Every exemplar is a native-macrophage (in-domain)
    real label; ``de_only`` keeps only informative up/down rows (the pool is ~99%
    ``none``). **Leak-free**: an exemplar matching the query's own ``(pert, gene)`` is
    always excluded, so a Traxler query never sees its own answer. Deterministic by seed.
    """
    src = labels_df[labels_df["label"] != "none"] if de_only else labels_df
    pool = [
        {"pert": str(r["pert"]), "gene": str(r["gene"]), "label": str(r["label"])}
        for r in src[["pert", "gene", "label"]].to_dict("records")
    ]

    def _provider(query_row: dict) -> "list[dict] | None":
        q = (str(query_row.get("pert")), str(query_row.get("gene")))
        candidates = [e for e in pool if (e["pert"], e["gene"]) != q]  # leak-free exclusion
        if not candidates:
            return None
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(candidates), size=min(n, len(candidates)), replace=False)
        return [candidates[i] for i in idx]

    return _provider
