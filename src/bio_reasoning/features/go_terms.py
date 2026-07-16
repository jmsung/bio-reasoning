"""GO:BP term features over a (perturbation, target-gene) pair.

The char-ngram features (`pair_features.py`) are at chance on the Track A OOD
split — gene symbols are arbitrary strings. GO:BP terms are not: they are a
shared biological vocabulary, so an unseen pert or target gene still lands on
terms seen in training. Crucially this encodes the **target gene**, the axis the
evidence prior ignores (it predicts one DE-confidence per pert regardless of
target). On the dual-OOD split this lifts mean AUROC from the prior's ~0.534 to
~0.56 (`scripts/two_stage_de_dir_eval.py`).

Encoding per pair: ``[pert-term BoW | target-term BoW | shared-term count]``.
The two vocabularies are fit on the train fold; the shared count is computed
from the raw term sets, so it survives vocabulary pruning.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import scipy.sparse as sp
from sklearn.feature_extraction.text import CountVectorizer

from bio_reasoning.features.gene_function import load_go_terms

_TOKEN = r"\S+"


def _doc(terms: list[str]) -> str:
    """Join a symbol's GO terms into a token doc (spaces within a term → '_')."""
    return " ".join(t.replace(" ", "_") for t in terms)


class GoPairFeaturizer:
    """Fit GO-term vocabularies for perts and target genes; encode pairs.

    ``pert_cache`` / ``gene_cache`` are JSON term caches (see
    :func:`load_go_terms`); symbols missing from a cache are fetched and
    persisted on first use, so ``transform`` works on unseen test symbols.
    """

    def __init__(self, pert_cache: str | Path, gene_cache: str | Path, min_df: int = 3):
        self.pert_cache = Path(pert_cache)
        self.gene_cache = Path(gene_cache)
        self.min_df = min_df

    def _terms(self, perts, genes) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
        return (
            load_go_terms(perts, self.pert_cache),
            load_go_terms(genes, self.gene_cache),
        )

    def fit(self, perts, genes) -> "GoPairFeaturizer":
        pterms, gterms = self._terms(perts, genes)
        self._cvp = CountVectorizer(token_pattern=_TOKEN, min_df=self.min_df, binary=True)
        self._cvg = CountVectorizer(token_pattern=_TOKEN, min_df=self.min_df, binary=True)
        self._cvp.fit([_doc(pterms[str(p)]) for p in perts])
        self._cvg.fit([_doc(gterms[str(g)]) for g in genes])
        self.n_features_ = len(self._cvp.vocabulary_) + len(self._cvg.vocabulary_) + 1
        return self

    def transform(self, perts, genes) -> sp.csr_matrix:
        pterms, gterms = self._terms(perts, genes)
        pert_bow = self._cvp.transform([_doc(pterms[str(p)]) for p in perts])
        gene_bow = self._cvg.transform([_doc(gterms[str(g)]) for g in genes])
        shared = np.array(
            [
                len(set(pterms[str(p)]) & set(gterms[str(g)]))
                for p, g in zip(perts, genes, strict=False)
            ],
            dtype=float,
        ).reshape(-1, 1)
        return sp.hstack([pert_bow, gene_bow, sp.csr_matrix(shared)], format="csr")
