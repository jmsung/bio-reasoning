"""Track A two-stage DE×DIR model — learned P(DE) and P(up|DE) heads.

The evidence prior (`track_a_prior.py`) fixes per-category constants for
P(up|DE) and DE-confidence. This model *learns* the same two quantities from
stateless pair-string features (`features/pair_features.py`), so it can pick up
signal the three hand-set categories miss while staying OOD-safe (no pert/gene
identity). It emits the metric's exact decomposition::

    up   = P(DE) · P(up | DE)
    down = P(DE) · (1 − P(up | DE))

so ``up + down`` is the DE score and ``up / (up + down)`` is the DIR score.

Both heads default to logistic regression — cheap, sparse-friendly, and it
yields calibrated-enough probabilities to multiply. Heads are injectable so the
eval script can swap in NB or a tree ensemble.
"""

from __future__ import annotations

import numpy as np
from sklearn.base import ClassifierMixin, clone
from sklearn.linear_model import LogisticRegression

from bio_reasoning.features.pair_features import CharNgramFeaturizer


def _default_head() -> LogisticRegression:
    return LogisticRegression(max_iter=1000, C=1.0)


def _fit_head(head: ClassifierMixin, X, y: np.ndarray):
    """Fit a binary head, or return the constant P(True) if ``y`` is single-class.

    sklearn classifiers raise on a single-class target; a fold can be all-`none`
    (DE head) or all one direction (DIR head). In that case there is nothing to
    learn — the answer is a constant, so short-circuit to ``float(class)``.
    """
    if len(np.unique(y)) < 2:
        return float(y[0]) if len(y) else 0.5
    return clone(head).fit(X, y)


def _proba_pos(head, X) -> np.ndarray:
    """P(class == True) from a fitted head or a constant produced by ``_fit_head``."""
    if isinstance(head, float):
        return np.full(X.shape[0], head)
    proba = head.predict_proba(X)
    classes = list(head.classes_)
    if True in classes:
        return proba[:, classes.index(True)]
    return np.full(X.shape[0], 0.5)


class TwoStageDEDIR:
    """Two classical heads recombined into graded up/down predictions."""

    def __init__(
        self,
        featurizer=None,
        de_head: ClassifierMixin | None = None,
        dir_head: ClassifierMixin | None = None,
    ):
        # Default features are the stateless char-ngrams; inject GoPairFeaturizer
        # for the OOD-effective GO-term features.
        self.featurizer = featurizer if featurizer is not None else CharNgramFeaturizer()
        self.de_head = de_head if de_head is not None else _default_head()
        self.dir_head = dir_head if dir_head is not None else _default_head()

    def fit(self, perts, genes, labels) -> "TwoStageDEDIR":
        labels = np.asarray(labels)
        self.featurizer.fit(perts, genes)
        X = self.featurizer.transform(perts, genes)

        de_y = labels != "none"
        self.de_ = _fit_head(self.de_head, X, de_y)

        m = de_y
        # DIR head sees only DE-positive rows — direction is undefined for none.
        self.dir_ = _fit_head(self.dir_head, X[m], labels[m] == "up")
        return self

    def predict(self, perts, genes) -> tuple[np.ndarray, np.ndarray]:
        """Return ``(pred_up, pred_down)`` aligned to the input pairs."""
        X = self.featurizer.transform(perts, genes)
        p_de = _proba_pos(self.de_, X)
        p_up = _proba_pos(self.dir_, X)
        up = p_de * p_up
        down = p_de * (1.0 - p_up)
        return up, down
