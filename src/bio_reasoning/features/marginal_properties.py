"""Marginal (per-symbol) DE features — pert breadth × gene responsiveness.

The five DE channels that failed were all *pair-interaction* (does this specific
pert-gene edge exist). This module tests the orthogonal **marginal** hypothesis:
some perturbations are broadly disruptive and some genes are broadly responsive,
independent of the pair. The transferable proxy is **network connectivity** — a
symbol's STRING interaction degree — which exists for unseen val symbols too, so
(unlike a train-derived DE rate) it survives the dual-OOD split.

``marginal_features`` returns a per-row ``[pert_degree, gene_degree]`` matrix; a
downstream head (fit on train) maps it to ``P(DE)``. Missing symbols get degree 0.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def marginal_features(
    perts: Sequence[str],
    genes: Sequence[str],
    degree: dict[str, float],
    log1p: bool = False,
) -> np.ndarray:
    """Return an ``(n, 2)`` array of ``[pert_degree, gene_degree]`` per (pert, gene).

    ``degree`` maps a symbol → its network connectivity (e.g. STRING partner count).
    Symbols absent from ``degree`` score 0 (uncovered). ``log1p`` compresses the
    heavy-tailed degree distribution while preserving order (recommended for a
    linear head).
    """
    p = np.array([float(degree.get(str(s), 0.0)) for s in perts])
    g = np.array([float(degree.get(str(s), 0.0)) for s in genes])
    if log1p:
        p = np.log1p(p)
        g = np.log1p(g)
    return np.column_stack([p, g])
