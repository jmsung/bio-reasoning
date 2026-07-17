"""Goal 1: gene-text embedding fetch + cache (GenePert substrate).

Embed each gene's text (GO:BP terms, falling back to the bare symbol) with an
OpenAI embedding model and cache the vectors to disk so repeated runs are
offline. The client is injectable so the whole path is testable without a key.
"""

import json

import numpy as np

from bio_reasoning.features.gene_embeddings import (
    build_gene_text,
    load_gene_embeddings,
)


class _FakeEmbeddings:
    """Deterministic stand-in for ``client.embeddings``; counts input texts seen."""

    def __init__(self) -> None:
        self.seen: list[str] = []

    def create(self, model, input):  # noqa: A002 — mirror the OpenAI kwarg name
        self.seen.extend(input)
        data = [type("E", (), {"embedding": [float(len(t)), float(len(t.split()))]}) for t in input]
        return type("R", (), {"data": data})


class _FakeClient:
    def __init__(self) -> None:
        self.embeddings = _FakeEmbeddings()


def test_build_gene_text_joins_go_terms_with_symbol_fallback(tmp_path):
    cache = tmp_path / "go.json"
    cache.write_text(json.dumps({"Rpl13": ["translation", "ribosome assembly"], "Xyz1": []}))
    text = build_gene_text(["Rpl13", "Xyz1"], cache)
    assert text["Rpl13"] == "translation ribosome assembly"
    assert text["Xyz1"] == "Xyz1"  # no GO terms → bare symbol


def test_embeds_and_caches_round_trip(tmp_path):
    gene_text = {"Rpl13": "translation ribosome", "Ifit1": "response to virus"}
    client = _FakeClient()
    cache = tmp_path / "emb.json"

    emb = load_gene_embeddings(gene_text, cache, client=client)
    assert set(emb) == set(gene_text)
    assert emb["Rpl13"].shape == (2,)
    assert np.allclose(emb["Rpl13"], [len("translation ribosome"), 2.0])
    assert len(client.embeddings.seen) == 2
    assert cache.exists()

    # cache hit → offline, no client required, identical vectors
    emb2 = load_gene_embeddings(gene_text, cache)
    assert np.allclose(emb2["Ifit1"], emb["Ifit1"])


def test_only_missing_symbols_are_fetched(tmp_path):
    cache = tmp_path / "emb.json"
    client = _FakeClient()
    load_gene_embeddings({"A": "aaa"}, cache, client=client)
    assert client.embeddings.seen == ["aaa"]

    # second call adds one new symbol → only the new text is embedded
    client2 = _FakeClient()
    emb = load_gene_embeddings({"A": "aaa", "B": "bbbb"}, cache, client=client2)
    assert client2.embeddings.seen == ["bbbb"]
    assert set(emb) == {"A", "B"}
