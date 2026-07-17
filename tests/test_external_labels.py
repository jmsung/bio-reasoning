"""Tests for the external (PerturbQA) label store + transfer-agreement gate."""

from __future__ import annotations

import pandas as pd

from bio_reasoning.features.external_labels import (
    classify_pert,
    to_human,
    transfer_agreement,
)


def test_to_human_uppercases_mouse_symbol():
    assert to_human("Psmd4") == "PSMD4"
    assert to_human("Anxa2") == "ANXA2"


def test_classify_pert_housekeeping_vs_immune():
    assert (
        classify_pert(["proteasome-mediated ubiquitin-dependent protein catabolic process"])
        == "housekeeping"
    )
    assert classify_pert(["macrophage activation involved in immune response"]) == "immune"
    assert classify_pert(["vasculogenesis", "osteoblast differentiation"]) == "other"


def _store(pairs):
    # pairs: {(PERT,GENE): (de_score, dir_score)} ; n filled as 1
    return {
        k: {"de_score": de, "dir_score": dr, "n_de": 1, "n_dir": 1 if dr is not None else 0}
        for k, (de, dr) in pairs.items()
    }


def test_transfer_agreement_perfect_de_and_dir():
    # Track A: two DE (up, down) + two none; external agrees perfectly.
    track = pd.DataFrame(
        {
            "pert": ["A", "A", "B", "B"],
            "gene": ["X", "Y", "X", "Y"],
            "label": ["up", "down", "none", "none"],
        }
    )
    store = _store(
        {
            ("A", "X"): (1.0, 1.0),
            ("A", "Y"): (1.0, 0.0),
            ("B", "X"): (0.0, None),
            ("B", "Y"): (0.0, None),
        }
    )
    r = transfer_agreement(track, store)
    assert r["de_auroc"] == 1.0  # external de_score perfectly ranks DE vs none
    assert r["dir_auroc"] == 1.0  # external dir_score perfectly ranks up vs down
    assert r["n_de"] == 4 and r["n_dir"] == 2


def test_transfer_agreement_anticorrelated_de_is_zero():
    track = pd.DataFrame({"pert": ["A", "B"], "gene": ["X", "Y"], "label": ["up", "none"]})
    store = _store({("A", "X"): (0.0, 1.0), ("B", "Y"): (1.0, None)})  # inverted DE
    r = transfer_agreement(track, store)
    assert r["de_auroc"] == 0.0


def test_transfer_agreement_ignores_pairs_absent_from_store():
    track = pd.DataFrame({"pert": ["A", "Z"], "gene": ["X", "W"], "label": ["up", "none"]})
    store = _store({("A", "X"): (1.0, 1.0)})  # Z/W absent → dropped
    r = transfer_agreement(track, store)
    assert r["n_de"] == 1
