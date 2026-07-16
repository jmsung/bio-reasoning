"""Char/prefix family-retrieval DE+direction channel (Goal 2).

For an unseen ``(pert, gene)`` pair, borrow the measured labels of TRAIN rows in
the same gene/pert *family* — the symbol with its trailing numeric index removed
(``Rpl13`` → ``rpl``). Aggregates into the two Track A buses: ``s_de`` = fraction
DE among borrowed rows, ``r`` = P(up | DE). Leak-free by the OOD split (val
identities are disjoint from train) and by an explicit exclude-own-pair guard.
"""

import numpy as np
import pandas as pd
import pytest

from bio_reasoning.features.family_retrieval import (
    FamilyRetriever,
    family_key,
    retrieve_family_labels,
)


def _train() -> pd.DataFrame:
    # ribosomal family (rpl*) → all up; interferon family (ifit*) → all down;
    # a lone housekeeping gene with no family peers.
    return pd.DataFrame(
        {
            "pert": ["Pa", "Pb", "Pc", "Pd", "Pe", "Pf", "Pg"],
            "gene": ["Rpl13", "Rpl7", "Rpl30", "Ifit1", "Ifit3", "Ifit2", "Actb"],
            "label": ["up", "up", "up", "down", "down", "down", "none"],
        }
    )


def test_family_key_strips_trailing_index_and_casefolds():
    assert family_key("Rpl13") == "rpl"
    assert family_key("Ifit3") == "ifit"
    assert family_key("Ifi44") == "ifi"
    assert family_key("Actb") == "actb"  # no trailing digits


def test_retrieve_borrows_same_family_labels():
    tr = _train()
    # unseen 'Rpl99' shares family 'rpl' with 3 all-up train rows
    s_de, r = retrieve_family_labels("Punseen", "Rpl99", tr, use_pert=False, use_gene=True)
    assert s_de == pytest.approx(1.0)  # all 3 borrowed rows are DE
    assert r == pytest.approx(1.0)  # all up


def test_retrieve_interferon_family_is_down():
    tr = _train()
    s_de, r = retrieve_family_labels("Punseen", "Ifit9", tr, use_pert=False, use_gene=True)
    assert s_de == pytest.approx(1.0)
    assert r == pytest.approx(0.0)  # all down


def test_uncovered_query_is_nan():
    tr = _train()
    s_de, r = retrieve_family_labels("Punseen", "Xyz1", tr, use_pert=False, use_gene=True)
    assert np.isnan(s_de) and np.isnan(r)


def test_min_support_threshold():
    tr = _train()
    # 'actb' family has 1 member; require 2 → uncovered
    s_de, r = retrieve_family_labels(
        "Punseen", "Actb2", tr, use_pert=False, use_gene=True, min_support=2
    )
    assert np.isnan(s_de)


def test_excludes_own_pair_no_leak():
    tr = _train()
    # query IS a train row (Pa, Rpl13); its own label must not be borrowed.
    # The other rpl rows (Rpl7, Rpl30) remain, so it still resolves — but the
    # guard means the row's own label never counts.
    s_de, r = retrieve_family_labels("Pa", "Rpl13", tr, use_pert=False, use_gene=True)
    # 2 remaining rpl rows, both up → still (1.0, 1.0), computed WITHOUT the own row
    assert s_de == pytest.approx(1.0) and r == pytest.approx(1.0)


def test_own_pair_is_only_family_member_is_nan():
    # a train row that is the sole member of its family → after excluding itself,
    # nothing to borrow → uncovered (proves the label can't leak from itself).
    tr = pd.DataFrame({"pert": ["Pa"], "gene": ["Solo1"], "label": ["up"]})
    s_de, r = retrieve_family_labels("Pa", "Solo1", tr, use_pert=False, use_gene=True)
    assert np.isnan(s_de) and np.isnan(r)


def test_pert_family_axis_retrieves():
    # retrieval on the pert axis: shared pert-family, gene axis off
    tr2 = pd.DataFrame(
        {
            "pert": ["Kras1", "Kras2", "Braf1"],
            "gene": ["Ga", "Gb", "Gc"],
            "label": ["up", "up", "down"],
        }
    )
    s_de, r = retrieve_family_labels("Kras9", "Gunseen", tr2, use_pert=True, use_gene=False)
    assert s_de == pytest.approx(1.0) and r == pytest.approx(1.0)  # both kras rows up


def test_channel_alignment_and_name():
    tr = _train()
    q = pd.DataFrame({"pert": ["Pu", "Pv"], "gene": ["Rpl99", "Nope1"]})
    ch = FamilyRetriever(use_pert=False, use_gene=True).fit(tr).channel(q)
    assert ch.name == "family_retrieval"
    assert len(ch) == 2
    assert ch.s_de[0] == pytest.approx(1.0)  # rpl family covered
    assert np.isnan(ch.s_de[1])  # 'nope' uncovered
