"""CollecTRI signed TF-regulon DE + direction feature over a (pert, gene) pair.

The Track A DE axis is at chance for every learned head we have tried, because
the OOD split shares no pert/gene identity with train. A curated TF→target
regulon is different: it encodes *mechanism*, not identity, so a regulon edge for
an unseen pert still fires. CollecTRI (`dc.op.collectri('mouse')`) supplies
~46k signed mouse edges — ``source`` (TF), ``target`` (gene), ``weight`` (+1
activating / -1 repressing) — attacking both dead axes at once:

* **DE** = the pair ``(pert, gene)`` is a regulon edge (the pert regulates the
  target). ``de_scores`` returns a 0/1 edge indicator.
* **DIRECTION** = the edge sign read under CRISPRi's fixed knockdown polarity.
  Knocking the TF down flips its normal effect, so an activating edge (+1)
  predicts the target goes **down** and a repressing edge (-1) predicts **up** —
  ``direction = -sign``. ``direction_scores`` returns +1 (up) / -1 (down) / 0.

Both are identity-free: the featurizer is constructed from the edge table alone,
so it transfers to the dual-OOD test split by construction. The network fetch is
cached to ``data/external`` by :func:`load_collectri_edges`; the featurizer and
coverage report are pure functions of the edge table and testable offline.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd


class TFRegulonFeaturizer:
    """Look up DE (edge indicator) and signed direction for ``(pert, gene)`` pairs.

    ``edges`` is a CollecTRI-shaped table with ``source_col`` (TF), ``target_col``
    (target gene) and ``weight_col`` (signed strength). Only the sign of the
    weight is used; ``weight >= 0`` is treated as activating. The lookup is built
    once at construction, so ``transform`` is O(1) per pair and safe on symbols
    absent from the network (they score 0).
    """

    def __init__(
        self,
        edges: pd.DataFrame,
        source_col: str = "source",
        target_col: str = "target",
        weight_col: str = "weight",
    ) -> None:
        self._sign: dict[tuple[str, str], int] = {}
        self._tfs: set[str] = set()
        for s, t, w in zip(edges[source_col], edges[target_col], edges[weight_col], strict=False):
            s, t = str(s), str(t)
            self._sign[(s, t)] = 1 if float(w) >= 0 else -1
            self._tfs.add(s)

    def is_tf(self, pert: str) -> bool:
        """True if ``pert`` is a regulator (edge source) in the network."""
        return str(pert) in self._tfs

    @staticmethod
    def _check(perts: Sequence[str], genes: Sequence[str]) -> None:
        if len(perts) != len(genes):
            raise ValueError("perts and genes must be the same length")

    def de_scores(self, perts: Sequence[str], genes: Sequence[str]) -> np.ndarray:
        """Return a 0/1 edge-indicator per pair (1.0 iff ``pert`` regulates ``gene``)."""
        self._check(perts, genes)
        return np.array(
            [
                1.0 if (str(p), str(g)) in self._sign else 0.0
                for p, g in zip(perts, genes, strict=True)
            ],
            dtype=float,
        )

    def direction_scores(self, perts: Sequence[str], genes: Sequence[str]) -> np.ndarray:
        """Return +1 (up) / -1 (down) / 0 (no edge) per pair under CRISPRi polarity.

        ``direction = -edge_sign``: activating (+1) → knockdown → target down (-1);
        repressing (-1) → up (+1). No edge → 0.
        """
        self._check(perts, genes)
        return np.array(
            [
                -float(self._sign.get((str(p), str(g)), 0))
                for p, g in zip(perts, genes, strict=True)
            ],
            dtype=float,
        )


def coverage_report(
    feat: TFRegulonFeaturizer,
    perts: Sequence[str],
    genes: Sequence[str],
) -> dict[str, float]:
    """Summarize how much of ``(perts, genes)`` the regulon can score.

    Coverage caps the achievable DE lift (a row with no covered TF pert gets no
    signal), so this is measured before any fusion. Returns ``n``, the fraction
    of rows whose pert is a covered TF (``tf_covered_frac``), the fraction that
    are actual regulon edges (``edge_frac``), and the edge fraction restricted to
    TF-pert rows (``edge_among_tf_frac``).
    """
    n = len(perts)
    if n == 0:
        return {"n": 0.0, "tf_covered_frac": 0.0, "edge_frac": 0.0, "edge_among_tf_frac": 0.0}
    tf_mask = np.array([feat.is_tf(p) for p in perts])
    edge = feat.de_scores(perts, genes).astype(bool)
    n_tf = int(tf_mask.sum())
    return {
        "n": float(n),
        "tf_covered_frac": float(tf_mask.mean()),
        "edge_frac": float(edge.mean()),
        "edge_among_tf_frac": float(edge[tf_mask].mean()) if n_tf else 0.0,
    }


def load_collectri_edges(
    cache_path: str | Path,
    organism: str = "mouse",
) -> pd.DataFrame:
    """Load CollecTRI edges from ``cache_path`` (CSV), fetching + caching on miss.

    On a cache miss, fetches signed regulons via ``decoupler`` (``dc.op.collectri``,
    with a fallback to the pre-2.0 ``dc.get_collectri``) and writes a normalized
    ``source,target,weight`` CSV to ``cache_path``. The fetch needs network +
    the ``network`` dependency group (``uv sync --group network``); everything
    downstream reads the cache.
    """
    cache = Path(cache_path)
    if cache.exists():
        return pd.read_csv(cache)

    import decoupler as dc  # optional; only needed on a cache miss

    if hasattr(dc, "op") and hasattr(dc.op, "collectri"):
        net = dc.op.collectri(organism=organism)
    else:  # decoupler < 2.0
        net = dc.get_collectri(organism=organism)

    net = net.rename(columns={"tf": "source"})[["source", "target", "weight"]]
    cache.parent.mkdir(parents=True, exist_ok=True)
    net.to_csv(cache, index=False)
    return net
