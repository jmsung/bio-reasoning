"""Tests for the Tahoe-100M drug-MoA transfer channel + coverage/oracle probe."""

from __future__ import annotations

import numpy as np
import pandas as pd

from bio_reasoning.features.tahoe_transfer import (
    coverage_report,
    covered_perts,
    perfect_oracle_channel,
    target_genes,
)

_TARGETS = {"DrugA": ["MTOR"], "DrugB": ["JAK1", "TYK2"], "DrugC": ["myc"]}


def test_target_genes_uppercases_and_dedupes():
    assert target_genes(_TARGETS) == {"MTOR", "JAK1", "TYK2", "MYC"}


def test_covered_perts_matches_on_uppercase_ortholog():
    # mouse title-case perts; only those that are a Tahoe drug target are covered.
    perts = ["Mtor", "Jak1", "Actl6a", "Arpc2", "Myc"]
    assert covered_perts(perts, _TARGETS) == {"Mtor", "Jak1", "Myc"}


def test_coverage_report_counts_rows_and_perts():
    df = pd.DataFrame(
        {
            "pert": ["Mtor", "Mtor", "Actl6a", "Arpc2"],
            "gene": ["X", "Y", "X", "Y"],
            "label": ["up", "none", "down", "up"],
        }
    )
    rep = coverage_report(df, _TARGETS)
    assert rep["n_rows_covered"] == 2  # the two Mtor rows
    assert rep["n_perts_covered"] == 1
    assert rep["covered_perts"] == ["Mtor"]
    assert 0.49 < rep["row_coverage"] < 0.51


def test_perfect_oracle_channel_true_labels_on_covered_only():
    df = pd.DataFrame(
        {
            "pert": ["Mtor", "Mtor", "Actl6a", "Arpc2"],
            "gene": ["X", "Y", "X", "Z"],
            "label": ["up", "none", "down", "up"],
        }
    )
    ch, covered = perfect_oracle_channel(df, df["label"].to_numpy(), _TARGETS)
    # Actl6a is uncovered -> NaN even though it is DE.
    assert covered.tolist() == [True, True, False, False]
    # covered DE rows carry the true DE score and direction; uncovered stay NaN.
    assert ch.s_de[0] == 1.0 and ch.r[0] == 1.0  # Mtor/X up
    assert ch.s_de[1] == 0.0 and ch.r[1] == 0.5  # Mtor/Y none
    assert np.isnan(ch.s_de[2]) and np.isnan(ch.s_de[3])


def test_perfect_oracle_channel_rejects_length_mismatch():
    df = pd.DataFrame({"pert": ["Mtor"], "gene": ["X"], "label": ["up"]})
    try:
        perfect_oracle_channel(df, np.array(["up", "down"]), _TARGETS)
    except ValueError:
        return
    raise AssertionError("expected ValueError on misaligned labels")
