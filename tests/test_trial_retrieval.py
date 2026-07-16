"""Offline tests for relevance-selected (retrieval) few-shot exemplars."""

from __future__ import annotations

import numpy as np
import pandas as pd

from bio_reasoning.trial_loop.loop import _make_examples_provider, retrieve_examples
from bio_reasoning.trial_loop.types import Variant


def _train(n: int = 20) -> pd.DataFrame:
    labels = ["up", "down", "none"]
    return pd.DataFrame(
        {
            "pert": [f"p{i}" for i in range(n)],
            "gene": [f"g{i}" for i in range(n)],
            "label": [labels[i % 3] for i in range(n)],
        }
    )


# Fake relevance key: category by parity of the pert index (A=even, B=odd).
def _cat(pert: str, gene: str = "") -> str:
    return "A" if int(pert[1:]) % 2 == 0 else "B"


def test_retrieve_examples_all_share_query_key() -> None:
    train = _train(20)
    keys = np.array([_cat(p) for p in train["pert"]], dtype=object)
    ex = retrieve_examples("A", train, keys, k=3, seed=0)
    assert ex is not None and len(ex) == 3
    assert all(_cat(e["pert"]) == "A" for e in ex)  # every exemplar is in-category


def test_retrieve_examples_tops_up_when_scarce() -> None:
    train = _train(20)
    keys = np.array(["A"] + ["B"] * 19, dtype=object)  # only p0 is category A
    ex = retrieve_examples("A", train, keys, k=3, seed=0)
    assert ex is not None and len(ex) == 3  # 1 in-category + 2 random top-up
    assert ex[0]["pert"] == "p0"  # the sole in-category exemplar comes first


def test_retrieve_examples_deterministic() -> None:
    train = _train(20)
    keys = np.array([_cat(p) for p in train["pert"]], dtype=object)
    assert retrieve_examples("A", train, keys, 3, seed=0) == retrieve_examples(
        "A", train, keys, 3, seed=0
    )


def test_provider_retrieves_in_category_per_row() -> None:
    train = _train(20)
    variant = Variant(id="go", n_few_shot=2, retrieval="go_category")
    provider = _make_examples_provider(train, variant, seed=0, key_fn=_cat)

    # Query perts are OOD (not in train); category by parity → A / B.
    ex_a = provider({"pert": "p100", "gene": "gX"})  # even → A
    ex_b = provider({"pert": "p101", "gene": "gY"})  # odd → B
    assert ex_a is not None and len(ex_a) == 2 and all(_cat(e["pert"]) == "A" for e in ex_a)
    assert ex_b is not None and all(_cat(e["pert"]) == "B" for e in ex_b)


def test_provider_random_is_row_independent() -> None:
    train = _train(20)
    variant = Variant(id="fs", n_few_shot=2, retrieval="random")
    provider = _make_examples_provider(train, variant, seed=0, key_fn=None)
    a = provider({"pert": "p1", "gene": "g"})
    b = provider({"pert": "p2", "gene": "g"})
    assert a == b and a is not None and len(a) == 2  # random → same fixed set for every row


def test_provider_none_for_zero_shot() -> None:
    provider = _make_examples_provider(
        _train(20), Variant(id="z", n_few_shot=0), seed=0, key_fn=_cat
    )
    assert provider({"pert": "p1", "gene": "g"}) is None
