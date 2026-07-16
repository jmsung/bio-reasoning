"""Stateless char-ngram + string-stat features over a (perturbation, gene) pair.

The Track A test split shares **zero** perturbations and **zero** target genes
with train (`docs/track-a-eda.md`), so any learned head must generalize from the
symbol *strings* themselves — not from identity, which never repeats. These
features are deliberately stateless: char n-grams are hashed (no fitted
vocabulary) and the string stats are pure functions of the pair, so the exact
same transform applies to unseen symbols. Gene families share naming (ribosomal
``Rpl*/Rps*``, interferon ``Ifit*``), so character n-grams carry real
functional signal that survives the OOD split.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import scipy.sparse as sp
from sklearn.feature_extraction.text import HashingVectorizer

# Char n-gram hash width per axis (pert, gene). The space of character 2–4grams
# over short gene symbols is small, so a few hundred buckets collide rarely.
NGRAM_FEATURES = 256
_NGRAM_KW = dict(
    analyzer="char_wb",
    ngram_range=(2, 4),
    n_features=NGRAM_FEATURES,
    alternate_sign=False,  # keep counts non-negative (NB-compatible)
    norm=None,
)

# Dense per-pair stats, in column order. All non-negative.
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
N_FEATURES = 2 * NGRAM_FEATURES + N_STRING_STATS


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


def extract_features(perts: Sequence[str], genes: Sequence[str]) -> sp.csr_matrix:
    """Return an ``(n_rows, N_FEATURES)`` sparse feature matrix for the pairs.

    Columns are ``[pert char-ngrams | gene char-ngrams | string stats]``.
    Stateless — no ``fit``, no vocabulary — so it is safe to apply unchanged to
    perturbations and genes never seen in training.
    """
    perts = [str(x) for x in perts]
    genes = [str(x) for x in genes]
    if len(perts) != len(genes):
        raise ValueError("perts and genes must be the same length")

    hv = HashingVectorizer(**_NGRAM_KW)
    if not perts:
        return sp.csr_matrix((0, N_FEATURES))

    pert_ng = hv.transform(perts)
    gene_ng = hv.transform(genes)
    stats = sp.csr_matrix(
        np.array([_string_stats(p, g) for p, g in zip(perts, genes, strict=False)], dtype=float)
    )
    return sp.hstack([pert_ng, gene_ng, stats], format="csr")


class CharNgramFeaturizer:
    """Stateless featurizer wrapper around :func:`extract_features`.

    Gives the char-ngram features the same ``fit``/``transform`` interface as
    the GO-term featurizer so either can be injected into ``TwoStageDEDIR``;
    ``fit`` is a no-op since there is no vocabulary to learn.
    """

    def fit(self, perts, genes) -> "CharNgramFeaturizer":
        return self

    def transform(self, perts, genes) -> sp.csr_matrix:
        return extract_features(perts, genes)
