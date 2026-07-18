"""Dense functional pair features for a tabular-FM (TabPFN) primary predictor.

The GO-term featurizer (`go_terms.py`) hands the learned heads a *sparse,
thousands-wide* bag-of-words — the wrong shape for TabPFN, which is happiest with
a compact (≲500) dense table. This module distills the same knowledge sources the
incumbent channels draw on (GO:BP terms, the STRING graph, gene-text embeddings)
into a small dense per-pair vector so TabPFN can act as the *primary* predictor
(framing #2 in `knowledge/wiki/findings/tabpfn-for-perturbation-tracks.md`), rather
than as a combiner over pre-scored channels (framing #1, already ruled out).

Every column is a pure function of ``(pert, gene)`` identity plus **static external
knowledge** — none is derived from train labels — so the matrix is leak-free on any
split, including the dual-OOD holdout where every pert and gene is unseen. There is
no ``fit``: an unseen symbol simply lands on its own GO terms / STRING degree /
embedding, exactly as a seen one does.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

# Dense per-pair columns, in order. All non-negative except emb_cosine ∈ [-1, 1].
FUNCTIONAL_FEATURE_NAMES = [
    "pert_go_count",
    "gene_go_count",
    "shared_go",
    "go_jaccard",
    "pert_degree",
    "gene_degree",
    "is_string_neighbour",
    "shared_string_neighbours",
    "neighbour_jaccard",
    "emb_cosine",
]


def _cosine(a: np.ndarray | None, b: np.ndarray | None) -> float:
    """Cosine similarity, or 0.0 (neutral) when either embedding is missing."""
    if a is None or b is None:
        return 0.0
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _jaccard(inter: int, union: int) -> float:
    return inter / union if union else 0.0


def _row(
    pert: str,
    gene: str,
    go_terms: dict[str, list[str]],
    partners: dict[str, set[str]],
    embeddings: dict[str, np.ndarray],
) -> list[float]:
    pg, gg = set(go_terms.get(pert, [])), set(go_terms.get(gene, []))
    shared_go = len(pg & gg)
    pp, gp = partners.get(pert, set()), partners.get(gene, set())
    shared_nb = len(pp & gp)
    return [
        float(len(pg)),
        float(len(gg)),
        float(shared_go),
        _jaccard(shared_go, len(pg | gg)),
        float(len(pp)),
        float(len(gp)),
        1.0 if pert in gp else 0.0,
        float(shared_nb),
        _jaccard(shared_nb, len(pp | gp)),
        _cosine(embeddings.get(pert), embeddings.get(gene)),
    ]


def functional_pair_features(
    perts: Sequence[str],
    genes: Sequence[str],
    *,
    go_terms: dict[str, list[str]],
    partners: dict[str, set[str]],
    embeddings: dict[str, np.ndarray],
) -> np.ndarray:
    """Return the ``(n_rows, len(FUNCTIONAL_FEATURE_NAMES))`` dense feature matrix.

    Columns follow :data:`FUNCTIONAL_FEATURE_NAMES`. Stateless — a pure function of
    each ``(pert, gene)`` pair and the passed-in knowledge dicts — so it applies
    unchanged to symbols never seen in train. ``go_terms``/``partners``/``embeddings``
    are the same caches the incumbent channels use, loaded once by the caller.
    """
    perts = [str(x) for x in perts]
    genes = [str(x) for x in genes]
    if len(perts) != len(genes):
        raise ValueError("perts and genes must be the same length")
    if not perts:
        return np.empty((0, len(FUNCTIONAL_FEATURE_NAMES)), dtype=np.float64)
    return np.array(
        [_row(p, g, go_terms, partners, embeddings) for p, g in zip(perts, genes, strict=True)],
        dtype=np.float64,
    )
