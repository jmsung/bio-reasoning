"""A learned combiner over the direction channels' per-row ``r``.

Logistic regression on the channel ``r`` values **plus their pairwise products**,
so it can capture non-linear interactions (e.g. "trust GO-DIR only when neighbour-DIR
is uncertain") that equal-weight or globally-weighted rank-fusion cannot. Uncovered
rows (``NaN``) are imputed to the neutral ``0.5``. Trains on DE rows only (``is_up``);
leak-free evaluation (out-of-fold / train-fold-only fitting) is the caller's job.
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression


def _features(r_matrix: np.ndarray) -> np.ndarray:
    """``(n, k)`` channel r's → ``(n, k + C(k,2))`` with NaN→0.5 and pairwise products."""
    x = np.where(np.isfinite(r_matrix), r_matrix, 0.5)
    k = x.shape[1]
    inters = [x[:, i] * x[:, j] for i in range(k) for j in range(i + 1, k)]
    return np.column_stack([x, *inters]) if inters else x


class DirectionStacker:
    """Fit ``P(up)`` from a row's channel-``r`` vector; a non-linear learned fuse."""

    def __init__(self, C: float = 1.0) -> None:
        self.C = C

    def fit(self, r_matrix: np.ndarray, is_up) -> "DirectionStacker":
        self.model_ = LogisticRegression(C=self.C, max_iter=1000).fit(
            _features(np.asarray(r_matrix, dtype=float)), np.asarray(is_up).astype(int)
        )
        return self

    def predict_up(self, r_matrix: np.ndarray) -> np.ndarray:
        """Return ``P(up)`` in ``[0, 1]`` per row."""
        return self.model_.predict_proba(_features(np.asarray(r_matrix, dtype=float)))[:, 1]
