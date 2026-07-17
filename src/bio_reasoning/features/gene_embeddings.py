"""Gene-text embeddings — the GenePert-style substrate for the DIRECTION channel.

Embed each gene's text (its GO:BP terms, falling back to the bare symbol when it
has none) with an OpenAI embedding model and cache the vectors to disk, so
repeated runs are offline. The vectors feed a leak-free ridge that predicts
perturbation *direction* (P(up|DE)) — reframed from DE (disproven) to direction
per the post-#28 strategy. The client is injectable so the fetch path is testable
without a live key.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from bio_reasoning.features.gene_function import load_go_terms
from bio_reasoning.models.fuse import Channel

_DEFAULT_MODEL = "text-embedding-3-small"


def build_gene_text(symbols, go_cache_path: str | Path) -> dict[str, str]:
    """Return ``{symbol: text-to-embed}`` — joined GO:BP terms, else the symbol.

    Reuses :func:`~bio_reasoning.features.gene_function.load_go_terms` (offline on
    a cache hit). A symbol with no GO terms falls back to its own name so it still
    embeds to a stable, meaningful vector.
    """
    terms = load_go_terms(symbols, go_cache_path)
    return {
        s: (" ".join(terms[s]) if terms.get(s) else s)
        for s in dict.fromkeys(symbols)  # unique, order-preserving
    }


def load_gene_embeddings(
    gene_text: dict[str, str],
    cache_path: str | Path,
    *,
    client=None,
    model: str | None = None,
) -> dict[str, np.ndarray]:
    """Return ``{symbol: embedding vector}``, caching vectors to disk.

    A cache hit is fully offline. On a miss the missing texts are embedded via
    ``client.embeddings.create`` (an OpenAI client, built lazily from the
    environment when ``client`` is ``None``) and persisted. Only symbols absent
    from the cache are fetched, so the batch grows incrementally across runs.
    """
    model = model or _DEFAULT_MODEL
    cache_path = Path(cache_path)
    cache: dict[str, list[float]] = {}
    if cache_path.exists():
        cache = json.loads(cache_path.read_text())

    missing = [s for s in dict.fromkeys(gene_text) if s not in cache]
    if missing:
        if client is None:
            from bio_reasoning.utils.openai_client import build_openai_client

            client = build_openai_client()
        resp = client.embeddings.create(model=model, input=[gene_text[s] for s in missing])
        for sym, item in zip(missing, resp.data, strict=True):
            cache[sym] = list(item.embedding)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache))

    return {s: np.asarray(cache[s], dtype=float) for s in gene_text}


def _pair_features(perts, genes, embeddings: dict[str, np.ndarray]) -> list[np.ndarray | None]:
    """Per row, ``[pert_emb ⊕ gene_emb]``; ``None`` when either symbol has no vector.

    Direction is driven mostly by the perturbation (housekeeping→up, immune→down,
    per the EDA); the gene embedding is included so the ridge can weight target
    identity too. A missing embedding marks the row uncovered (``NaN`` downstream).
    """
    out: list[np.ndarray | None] = []
    for p, g in zip(perts, genes, strict=True):
        pe, ge = embeddings.get(p), embeddings.get(g)
        out.append(None if pe is None or ge is None else np.concatenate([pe, ge]))
    return out


def fit_direction_ridge(
    train_df: pd.DataFrame, embeddings: dict[str, np.ndarray], *, alpha: float = 1.0
) -> Ridge:
    """Fit a GenePert-style ridge mapping ``[pert_emb ⊕ gene_emb] → P(up|DE)``.

    Trained on TRAIN **DE rows only** (``label`` in ``{up, down}``), target ``1``
    for ``up`` / ``0`` for ``down`` — so it is leak-free: query labels are never
    seen, and the embedding features let it transfer to unseen perts/genes. Rows
    whose pert or gene lacks an embedding are dropped from the fit.
    """
    de = train_df[train_df["label"] != "none"]
    feats = _pair_features(de["pert"], de["gene"], embeddings)
    x_rows, y = [], []
    for f, label in zip(feats, de["label"], strict=True):
        if f is not None:
            x_rows.append(f)
            y.append(1.0 if label == "up" else 0.0)
    if not x_rows:
        raise ValueError("no DE train rows with embeddings to fit the direction ridge")
    return Ridge(alpha=alpha).fit(np.vstack(x_rows), np.asarray(y))


def gene_embedding_channel(
    queries: pd.DataFrame, ridge: Ridge, embeddings: dict[str, np.ndarray]
) -> Channel:
    """Score ``queries`` with the fitted ridge → a direction-only :class:`Channel`.

    ``r`` = clipped ``P(up|DE)`` per row; rows missing an embedding are ``NaN``
    (uncovered) so :func:`~bio_reasoning.models.fuse.fuse` falls back to other
    channels. Carries no ``s_de`` — DE is disproven; this is a direction lever.
    """
    feats = _pair_features(queries["pert"], queries["gene"], embeddings)
    r = np.full(len(feats), np.nan)
    covered = [i for i, f in enumerate(feats) if f is not None]
    covered_feats = [f for f in feats if f is not None]
    if covered_feats:
        preds = ridge.predict(np.vstack(covered_feats))
        r[covered] = np.clip(preds, 0.0, 1.0)
    return Channel(name="gene_embedding", r=r)
