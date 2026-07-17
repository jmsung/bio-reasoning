"""Tests for the Traxler leak-free exemplar pool."""

from __future__ import annotations

import pandas as pd

from bio_reasoning.data.traxler_labels import make_traxler_exemplar_pool


def _labels() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "pert": ["A", "A", "B", "B", "C"],
            "gene": ["g1", "g2", "g3", "g4", "g5"],
            "label": ["up", "down", "up", "none", "down"],
            "log2fc": [1.2, -1.5, 1.1, 0.2, -2.0],
        }
    )


def test_returns_in_domain_exemplars_from_the_pool():
    pool = make_traxler_exemplar_pool(_labels(), n=2, seed=0)
    ex = pool({"pert": "Query", "gene": "qg"})
    assert ex is not None and len(ex) == 2
    keys = {(e["pert"], e["gene"]) for e in _labels().to_dict("records")}
    assert all((e["pert"], e["gene"]) in keys for e in ex)
    assert all(set(e) == {"pert", "gene", "label"} for e in ex)


def test_de_only_excludes_none_by_default():
    pool = make_traxler_exemplar_pool(_labels(), n=4, seed=0)
    ex = pool({"pert": "Q", "gene": "q"})
    assert all(e["label"] in {"up", "down"} for e in ex)  # the 'none' row (B,g4) never appears


def test_leak_free_excludes_the_query_row():
    # a query that IS in the pool must never be handed its own label
    pool = make_traxler_exemplar_pool(_labels(), n=10, seed=0)  # n > pool → all others
    ex = pool({"pert": "A", "gene": "g1"})
    assert ("A", "g1") not in {(e["pert"], e["gene"]) for e in ex}


def test_deterministic_given_seed():
    a = make_traxler_exemplar_pool(_labels(), n=2, seed=7)({"pert": "Q", "gene": "q"})
    b = make_traxler_exemplar_pool(_labels(), n=2, seed=7)({"pert": "Q", "gene": "q"})
    assert a == b


def test_includes_none_when_de_only_false():
    pool = make_traxler_exemplar_pool(_labels(), n=5, seed=0, de_only=False)
    ex = pool({"pert": "Q", "gene": "q"})
    assert any(e["label"] == "none" for e in ex)
