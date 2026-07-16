"""Char n-gram TF-IDF pair featurizer (Goal 1).

The old featurizer hashed char n-grams into 256 colliding buckets with no
TF-IDF, so the string signal was destroyed and a head on it scored ~chance. The
fix is a proper char n-gram **TF-IDF** (`CharNgramFeaturizer`): stateful (IDF is
fit on the train fold) but still OOD-safe — an unseen symbol's 2–4-grams mostly
overlap n-grams seen in train (gene families share substrings), so they transfer.
These tests pin the fit/transform contract, unseen-symbol transfer, and — the
regression that matters — that a family-separable signal is now linearly
recoverable, which the collision-limited version could not do.
"""

import numpy as np
import pytest
import scipy.sparse as sp
from sklearn.linear_model import LogisticRegression

from bio_reasoning.features.pair_features import (
    N_STRING_STATS,
    CharNgramFeaturizer,
    string_stats,
)


def _family_dataset():
    """Two gene families with shared prefixes → opposite labels (up vs down).

    'Rpl*/Rps*' ribosomal → up; 'Ifit*/Ifi*' interferon → down. The perts are
    irrelevant noise; only the target-gene family carries the signal.
    """
    up_genes = ["Rpl13", "Rpl7", "Rps6", "Rps19", "Rpl30", "Rps3"]
    dn_genes = ["Ifit1", "Ifit3", "Ifi44", "Ifit2", "Ifi27", "Ifit5"]
    genes = up_genes + dn_genes
    perts = [f"P{i}" for i in range(len(genes))]
    y = np.array([1] * len(up_genes) + [0] * len(dn_genes))
    return perts, genes, y


def test_fit_learns_char_vocabulary():
    perts, genes, _ = _family_dataset()
    f = CharNgramFeaturizer().fit(perts, genes)
    # a real vocabulary is learned beyond the fixed dense string stats
    assert f.n_features_ > N_STRING_STATS


def test_transform_width_matches_fit():
    perts, genes, _ = _family_dataset()
    f = CharNgramFeaturizer().fit(perts, genes)
    X = f.transform(perts, genes)
    assert sp.issparse(X)
    assert X.shape == (len(perts), f.n_features_)


def test_deterministic_across_calls():
    perts, genes, _ = _family_dataset()
    f = CharNgramFeaturizer().fit(perts, genes)
    a = f.transform(["P0"], ["Rpl13"]).toarray()
    b = f.transform(["P0"], ["Rpl13"]).toarray()
    assert np.array_equal(a, b)


def test_unseen_symbol_transfers_via_shared_ngrams():
    # A never-seen ribosomal symbol still lights up char-ngram columns because
    # its 2–4-grams overlap the trained 'Rpl'/'Rps' families.
    perts, genes, _ = _family_dataset()
    f = CharNgramFeaturizer().fit(perts, genes)
    X = f.transform(["Pnew"], ["Rpl99"])
    ngram_block = X[:, :-N_STRING_STATS]
    assert ngram_block.nnz > 0
    assert X.shape == (1, f.n_features_)


def test_family_signal_is_linearly_separable():
    # The regression: fit featurizer + a linear head on the families, then
    # classify a held-out symbol from each family. The collision-limited,
    # no-TF-IDF version scored ~chance here; TF-IDF recovers the signal.
    perts, genes, y = _family_dataset()
    f = CharNgramFeaturizer().fit(perts, genes)
    clf = LogisticRegression(max_iter=1000).fit(f.transform(perts, genes), y)
    Xtest = f.transform(["Pa", "Pb"], ["Rpl99", "Ifit99"])
    pred = clf.predict(Xtest)
    assert pred.tolist() == [1, 0]  # unseen ribosomal → up, unseen interferon → down


def test_string_stats_capture_shared_prefix():
    S = string_stats(["Abcd", "Xyz"], ["Abef", "Qrs"]).toarray()
    assert S.shape == (2, N_STRING_STATS)
    assert S[0, 6] == 2  # 'Abcd' / 'Abef' share prefix 'Ab'
    assert S[1, 6] == 0  # 'Xyz' / 'Qrs' share nothing


def test_length_mismatch_raises():
    f = CharNgramFeaturizer()
    with pytest.raises(ValueError):
        f.fit(["a"], ["b", "c"])


def test_empty_transform_is_zero_by_width():
    perts, genes, _ = _family_dataset()
    f = CharNgramFeaturizer().fit(perts, genes)
    X = f.transform([], [])
    assert X.shape == (0, f.n_features_)
