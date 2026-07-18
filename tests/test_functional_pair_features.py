"""Tests for the dense functional pair-feature matrix (TabPFN primary predictor).

The features are pure functions of ``(pert, gene)`` identity plus external static
knowledge (GO terms, STRING graph, gene embeddings) — they never see labels, so
the matrix is leak-free by construction on any split.
"""

from __future__ import annotations

import numpy as np

from bio_reasoning.features.functional_pair_features import (
    FUNCTIONAL_FEATURE_NAMES,
    functional_pair_features,
)

GO = {
    "A": ["GO:1", "GO:2", "GO:3"],
    "B": ["GO:2", "GO:3"],
    "C": [],
}
PARTNERS = {
    "A": {"B", "X", "Y"},
    "B": {"A", "Y"},
    "C": set(),
}
EMB = {
    "A": np.array([1.0, 0.0]),
    "B": np.array([1.0, 0.0]),
    "C": np.array([0.0, 1.0]),
}


def _col(x: np.ndarray, name: str) -> np.ndarray:
    return x[:, FUNCTIONAL_FEATURE_NAMES.index(name)]


def test_shape_and_names() -> None:
    x = functional_pair_features(
        ["A", "B"], ["B", "C"], go_terms=GO, partners=PARTNERS, embeddings=EMB
    )
    assert x.shape == (2, len(FUNCTIONAL_FEATURE_NAMES))
    assert x.dtype == np.float64


def test_go_overlap_columns() -> None:
    # A GO {1,2,3}, B GO {2,3}: shared = 2, union = 3, jaccard = 2/3.
    x = functional_pair_features(["A"], ["B"], go_terms=GO, partners=PARTNERS, embeddings=EMB)
    assert _col(x, "pert_go_count")[0] == 3.0
    assert _col(x, "gene_go_count")[0] == 2.0
    assert _col(x, "shared_go")[0] == 2.0
    assert abs(_col(x, "go_jaccard")[0] - 2.0 / 3.0) < 1e-9


def test_string_degree_and_adjacency() -> None:
    # A partners {B,X,Y} (deg 3), B partners {A,Y} (deg 2), A-B is a direct edge,
    # shared neighbours {Y}=1, union {A,B,X,Y}=4 → jaccard 1/4.
    x = functional_pair_features(["A"], ["B"], go_terms=GO, partners=PARTNERS, embeddings=EMB)
    assert _col(x, "pert_degree")[0] == 3.0
    assert _col(x, "gene_degree")[0] == 2.0
    assert _col(x, "is_string_neighbour")[0] == 1.0
    assert _col(x, "shared_string_neighbours")[0] == 1.0
    assert abs(_col(x, "neighbour_jaccard")[0] - 0.25) < 1e-9


def test_non_adjacent_pair() -> None:
    # A and C are not STRING partners.
    x = functional_pair_features(["A"], ["C"], go_terms=GO, partners=PARTNERS, embeddings=EMB)
    assert _col(x, "is_string_neighbour")[0] == 0.0


def test_embedding_cosine() -> None:
    # A,B identical vectors → cos 1; A,C orthogonal → cos 0.
    x = functional_pair_features(
        ["A", "A"], ["B", "C"], go_terms=GO, partners=PARTNERS, embeddings=EMB
    )
    assert abs(_col(x, "emb_cosine")[0] - 1.0) < 1e-9
    assert abs(_col(x, "emb_cosine")[1] - 0.0) < 1e-9


def test_missing_symbol_defaults() -> None:
    # Unknown symbols: zero GO/degree/neighbours, neutral cosine 0.
    x = functional_pair_features(["Z"], ["Q"], go_terms=GO, partners=PARTNERS, embeddings=EMB)
    assert _col(x, "pert_go_count")[0] == 0.0
    assert _col(x, "gene_go_count")[0] == 0.0
    assert _col(x, "shared_go")[0] == 0.0
    assert _col(x, "go_jaccard")[0] == 0.0
    assert _col(x, "pert_degree")[0] == 0.0
    assert _col(x, "is_string_neighbour")[0] == 0.0
    assert _col(x, "emb_cosine")[0] == 0.0


def test_leak_free_stateless() -> None:
    # Pure function of identity + KB: no label input, deterministic across calls.
    a = functional_pair_features(
        ["A", "B"], ["B", "C"], go_terms=GO, partners=PARTNERS, embeddings=EMB
    )
    b = functional_pair_features(
        ["A", "B"], ["B", "C"], go_terms=GO, partners=PARTNERS, embeddings=EMB
    )
    assert np.array_equal(a, b)


def test_empty_input() -> None:
    x = functional_pair_features([], [], go_terms=GO, partners=PARTNERS, embeddings=EMB)
    assert x.shape == (0, len(FUNCTIONAL_FEATURE_NAMES))
