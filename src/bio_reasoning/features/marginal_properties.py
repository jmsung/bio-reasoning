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
    essentiality: dict[str, float] | None = None,
) -> np.ndarray:
    """Per-(pert, gene) marginal features: ``[pert_degree, gene_degree]``.

    ``degree`` maps a symbol → its network connectivity (e.g. STRING partner count).
    Symbols absent from ``degree`` score 0 (uncovered). ``log1p`` compresses the
    heavy-tailed degree distribution while preserving order (recommended for a
    linear head).

    When ``essentiality`` is given (symbol → gene-effect score, DepMap convention
    where more-negative = more essential), two more columns are appended:
    ``[pert_ess, gene_ess]``. Missing symbols score 0.0 (non-essential). ``log1p``
    applies **only** to the non-negative degree columns, never the signed score.
    """
    p = np.array([float(degree.get(str(s), 0.0)) for s in perts])
    g = np.array([float(degree.get(str(s), 0.0)) for s in genes])
    if log1p:
        p = np.log1p(p)
        g = np.log1p(g)
    cols = [p, g]
    if essentiality is not None:
        cols.append(np.array([float(essentiality.get(str(s), 0.0)) for s in perts]))
        cols.append(np.array([float(essentiality.get(str(s), 0.0)) for s in genes]))
    return np.column_stack(cols)
