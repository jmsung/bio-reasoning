"""Goal 1 tests for the stateless (pert, gene) pair feature extractor.

The Track A test split shares zero perturbations and zero genes with train, so
the extractor must be stateless (no fitted vocabulary) and produce a
fixed-width row for any symbol pair, seen or unseen. These tests pin the shape,
determinism, unseen-symbol safety, and the string-stat semantics.
"""

import numpy as np
import pytest
import scipy.sparse as sp

from bio_reasoning.features.pair_features import (
    N_FEATURES,
    N_STRING_STATS,
    extract_features,
)


def test_shape_matches_rows_and_fixed_width():
    X = extract_features(["Psmd4", "Cul2"], ["Anxa2", "Upp1"])
    assert sp.issparse(X)
    assert X.shape == (2, N_FEATURES)


def test_deterministic_across_calls():
    a = extract_features(["Rpl13"], ["Rps6"]).toarray()
    b = extract_features(["Rpl13"], ["Rps6"]).toarray()
    assert np.array_equal(a, b)


def test_handles_unseen_symbols_without_fit():
    # Symbols never seen at "train" time still produce a full-width row — the
    # extractor holds no vocabulary, so OOD perts/genes are not special.
    X = extract_features(["ZZZ999"], ["QQQ000"])
    assert X.shape == (1, N_FEATURES)


def test_string_stats_capture_shared_prefix():
    # Dense string stats occupy the last N_STRING_STATS columns; shared_prefix
    # is column index 6 within that block.
    X = extract_features(["Abcd", "Xyz"], ["Abef", "Qrs"]).toarray()
    stats = X[:, -N_STRING_STATS:]
    assert stats[0, 6] == 2  # 'Abcd' / 'Abef' share prefix 'Ab'
    assert stats[1, 6] == 0  # 'Xyz' / 'Qrs' share nothing


def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        extract_features(["a"], ["b", "c"])


def test_empty_input_is_zero_by_width():
    X = extract_features([], [])
    assert X.shape == (0, N_FEATURES)
