"""Goal 2: CORE contrastive-evidence builder.

For a query (pert, gene), retrieve neighbour train rows and split into POSITIVE
(differentially expressed: up/down) vs NEGATIVE (none) references. Leak-free:
train-only, excludes the query's own pair.
"""

import pandas as pd

from bio_reasoning.features.contrastive_context import contrastive_references


def _train() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "pert": ["Pa", "Pa", "Pb", "Pc", "Q"],
            "gene": ["G1", "G2", "G1", "G3", "G1"],
            "label": ["up", "none", "down", "none", "up"],
        }
    )


def test_splits_positive_negative_leak_free():
    train = _train()
    # Q's neighbours include itself (to prove the own-pair is still excluded)
    pn = {"Q": {"Pa", "Pb", "Q"}}
    gn = {"G1": {"G2"}}
    refs = contrastive_references("Q", "G1", train, pn, gn, min_support=1)

    all_refs = refs["positive"] + refs["negative"]
    assert ("Q", "G1", "up") not in all_refs  # own pair excluded → leak-free
    assert {lab for _, _, lab in refs["positive"]} <= {"up", "down"}
    assert {lab for _, _, lab in refs["negative"]} == {"none"}
    assert ("Pa", "G1", "up") in refs["positive"]
    assert ("Pb", "G1", "down") in refs["positive"]
    assert ("Pa", "G2", "none") in refs["negative"]


def test_thin_evidence_returns_empty():
    train = _train()
    refs = contrastive_references("Zzz", "Gzz", train, {}, {}, min_support=1)
    assert refs == {"positive": [], "negative": []}
