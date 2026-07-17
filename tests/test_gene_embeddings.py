"""Goal 1: gene-text embedding fetch + cache (GenePert substrate).

Embed each gene's text (GO:BP terms, falling back to the bare symbol) with an
OpenAI embedding model and cache the vectors to disk so repeated runs are
offline. The client is injectable so the whole path is testable without a key.
"""

import json

import numpy as np
import pandas as pd

from bio_reasoning.features.gene_embeddings import (
    build_gene_text,
    fit_direction_ridge,
    gene_embedding_channel,
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


# --- Goal 2: GenePert-style DIR ridge -------------------------------------


def _emb(sign: float) -> np.ndarray:
    return np.array([sign, 0.1])


def _dir_setup():
    """Direction driven by pert sign (+ = up / housekeeping-like, - = down / immune)."""
    train = pd.DataFrame(
        {
            "pert": ["Ha", "Hb", "Ia", "Ib", "Ha"],
            "gene": ["G1", "G2", "G1", "G2", "G3"],
            "label": ["up", "up", "down", "down", "none"],
        }
    )
    emb = {
        "Ha": _emb(1),
        "Hb": _emb(1),
        "Ia": _emb(-1),
        "Ib": _emb(-1),
        "G1": _emb(0),
        "G2": _emb(0),
        "G3": _emb(0),
        "Hc": _emb(1),
        "Ic": _emb(-1),
        "G9": _emb(0),
    }
    return train, emb


def test_ridge_recovers_direction_on_unseen_perts():
    train, emb = _dir_setup()
    ridge = fit_direction_ridge(train, emb)
    q = pd.DataFrame({"pert": ["Hc", "Ic"], "gene": ["G9", "G9"]})  # both perts unseen in train
    ch = gene_embedding_channel(q, ridge, emb)
    assert ch.name == "gene_embedding"
    assert ch.s_de is None and ch.r is not None
    assert ch.r[0] > ch.r[1]  # housekeeping-like → more up than immune-like
    assert np.all((ch.r[np.isfinite(ch.r)] >= 0) & (ch.r[np.isfinite(ch.r)] <= 1))


def test_channel_marks_uncovered_rows_nan():
    train, emb = _dir_setup()
    ridge = fit_direction_ridge(train, emb)
    q = pd.DataFrame({"pert": ["UNKNOWN", "Hc"], "gene": ["G9", "MISSING"]})
    ch = gene_embedding_channel(q, ridge, emb)
    assert np.isnan(ch.r[0])  # unknown pert embedding → uncovered
    assert np.isnan(ch.r[1])  # unknown gene embedding → uncovered


def test_fit_uses_de_rows_only():
    train, emb = _dir_setup()
    # a 'none' row with a wild pert embedding must not perturb the fit (excluded)
    poisoned = pd.concat(
        [train, pd.DataFrame({"pert": ["Z"], "gene": ["G1"], "label": ["none"]})],
        ignore_index=True,
    )
    emb2 = {**emb, "Z": _emb(999)}
    r_clean = fit_direction_ridge(train, emb).predict(np.concatenate([_emb(1), _emb(0)])[None, :])
    r_poison = fit_direction_ridge(poisoned, emb2).predict(
        np.concatenate([_emb(1), _emb(0)])[None, :]
    )
    assert np.allclose(r_clean, r_poison)
