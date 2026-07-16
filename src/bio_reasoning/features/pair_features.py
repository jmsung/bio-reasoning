"""Char n-gram TF-IDF + string-stat features over a (perturbation, gene) pair.

The Track A test split shares **zero** perturbations and **zero** target genes
with train (`docs/track-a-eda.md`), so any learned head must generalize from the
symbol *strings* themselves — not identity, which never repeats. Gene families
share naming (ribosomal ``Rpl*/Rps*``, interferon ``Ifit*``), so character
n-grams carry real functional signal that survives the OOD split.

An earlier version hashed the n-grams into 256 colliding buckets with **no
TF-IDF**, which destroyed that signal (a head on it scored ~chance, 0.531). This
module fits a proper char n-gram **TF-IDF** per axis (:class:`CharNgramFeaturizer`).
It is stateful — the vocabulary and IDF are fit on the train fold — but stays
OOD-safe: an unseen symbol's 2–4-grams overlap n-grams seen in train, so the same
weighted representation applies to symbols never seen at fit time (novel n-grams
are simply dropped). The dense per-pair string stats remain a stateless pure
function of the pair.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer

# Char n-gram TF-IDF range, shared by the pert and gene axes.
_NGRAM_RANGE = (2, 4)

# Dense per-pair stats, in column order. All non-negative, stateless.
STRING_STAT_NAMES = [
    "len_pert",
    "len_gene",
    "digits_pert",
    "digits_gene",
    "upper_pert",
    "upper_gene",
    "shared_prefix",
    "trigram_jaccard",
    "pert_ends_digit",
    "gene_ends_digit",
]
N_STRING_STATS = len(STRING_STAT_NAMES)


def _char_trigrams(s: str) -> set[str]:
    s = f"<{s}>"
    return {s[i : i + 3] for i in range(max(len(s) - 2, 1))}


def _string_stats(pert: str, gene: str) -> list[float]:
    p, g = pert, gene
    pt, gt = _char_trigrams(p), _char_trigrams(g)
    union = len(pt | gt) or 1
    prefix = 0
    for a, b in zip(p, g, strict=False):
        if a != b:
            break
        prefix += 1
    return [
        float(len(p)),
        float(len(g)),
        float(sum(c.isdigit() for c in p)),
        float(sum(c.isdigit() for c in g)),
        float(sum(c.isupper() for c in p)),
        float(sum(c.isupper() for c in g)),
        float(prefix),
        len(pt & gt) / union,
        float(p[-1:].isdigit()),
        float(g[-1:].isdigit()),
    ]


def string_stats(perts: Sequence[str], genes: Sequence[str]) -> sp.csr_matrix:
    """Return the ``(n_rows, N_STRING_STATS)`` dense per-pair string stats.

    Stateless — a pure function of each ``(pert, gene)`` pair — so it applies
    unchanged to unseen symbols. Columns follow :data:`STRING_STAT_NAMES`.
    """
    perts = [str(x) for x in perts]
    genes = [str(x) for x in genes]
    if len(perts) != len(genes):
        raise ValueError("perts and genes must be the same length")
    if not perts:
        return sp.csr_matrix((0, N_STRING_STATS))
    return sp.csr_matrix(
        np.array([_string_stats(p, g) for p, g in zip(perts, genes, strict=True)], dtype=float)
    )


class CharNgramFeaturizer:
    """Char n-gram TF-IDF over ``(pert, gene)`` + stateless string stats.

    Fits one :class:`~sklearn.feature_extraction.text.TfidfVectorizer` per axis
    on the train symbols (``analyzer="char_wb"``, 2–4grams, L2-normalized,
    ``sublinear_tf``). ``transform`` concatenates
    ``[pert-tfidf | gene-tfidf | string-stats]``. Fit/transform is the standard
    leak-free lifecycle (``fit`` on train, ``transform`` on eval); the width is
    ``n_features_`` after fit. Exposes the same ``fit``/``transform`` interface as
    the GO-term featurizer so either injects into ``TwoStageDEDIR``.
    """

    def __init__(self, ngram_range: tuple[int, int] = _NGRAM_RANGE, min_df: int = 2):
        self.ngram_range = ngram_range
        self.min_df = min_df

    def _new_vectorizer(self) -> TfidfVectorizer:
        return TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=self.ngram_range,
            min_df=self.min_df,
            sublinear_tf=True,
            norm="l2",
        )

    def _fit_vectorizer(self, docs: list[str]) -> TfidfVectorizer:
        """Fit a char-TFIDF vectorizer, backing off to ``min_df=1`` on empty vocab.

        With ``min_df>1`` a tiny corpus whose n-grams are all rare raises "empty
        vocabulary"; fall back so the featurizer degrades gracefully instead of
        crashing (mirrors the GO featurizer).
        """
        try:
            return self._new_vectorizer().fit(docs)
        except ValueError:
            v = self._new_vectorizer()
            v.min_df = 1
            return v.fit(docs)

    def fit(self, perts, genes) -> "CharNgramFeaturizer":
        perts = [str(x) for x in perts]
        genes = [str(x) for x in genes]
        if len(perts) != len(genes):
            raise ValueError("perts and genes must be the same length")
        self._vp = self._fit_vectorizer(perts)
        self._vg = self._fit_vectorizer(genes)
        self.n_features_ = len(self._vp.vocabulary_) + len(self._vg.vocabulary_) + N_STRING_STATS
        return self

    def transform(self, perts, genes) -> sp.csr_matrix:
        perts = [str(x) for x in perts]
        genes = [str(x) for x in genes]
        if len(perts) != len(genes):
            raise ValueError("perts and genes must be the same length")
        if not perts:
            return sp.csr_matrix((0, self.n_features_))
        pert_ng = self._vp.transform(perts)
        gene_ng = self._vg.transform(genes)
        return sp.hstack([pert_ng, gene_ng, string_stats(perts, genes)], format="csr")
