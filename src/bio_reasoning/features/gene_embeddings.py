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

from bio_reasoning.features.gene_function import load_go_terms

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
