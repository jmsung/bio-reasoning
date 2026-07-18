"""DepMap co-essentiality neighbour key.

Genes with correlated CRISPR dependency profiles across cell lines are functionally
co-regulated — a different co-regulation graph than STRING. We turn the gene-effect
matrix into a neighbour graph (each gene → its top-k most co-essential partners) that
drops into the same label-borrowing direction channel as the STRING graph, but keyed
on co-essentiality instead of physical/annotation interaction.
"""

import numpy as np
import pandas as pd

from bio_reasoning.features.coessentiality import (
    coessential_partners,
    map_partners_to_universe,
    parse_effect_columns,
)


def test_parse_effect_columns_strips_entrez_and_uppercases():
    m = parse_effect_columns(["Unnamed: 0", "A1BG (1)", "Actb (11461)"])
    assert m == {"A1BG": "A1BG (1)", "ACTB": "Actb (11461)"}


def test_coessential_partners_ranks_by_absolute_correlation():
    # G0 tracks G1 tightly (+), anti-tracks G2 (−), unrelated to G3.
    corr = pd.DataFrame(
        [
            [1.0, 0.9, -0.8, 0.05],
            [0.9, 1.0, -0.7, 0.02],
            [-0.8, -0.7, 1.0, 0.01],
            [0.05, 0.02, 0.01, 1.0],
        ],
        index=["G0", "G1", "G2", "G3"],
        columns=["G0", "G1", "G2", "G3"],
    )
    part = coessential_partners(corr, top_k=2, min_corr=0.3)
    # co-essentiality is a functional-similarity graph → positive correlation only,
    # ranked by strength; self excluded; below-threshold (G3) excluded.
    assert part["G0"] == ["G1"]
    assert part["G1"] == ["G0"]
    assert part["G2"] == []  # only negative correlations → no co-essential partner
    assert part["G3"] == []


def test_coessential_partners_top_k_caps_neighbours():
    corr = pd.DataFrame(
        [
            [1.0, 0.9, 0.8, 0.7],
            [0.9, 1.0, 0.1, 0.1],
            [0.8, 0.1, 1.0, 0.1],
            [0.7, 0.1, 0.1, 1.0],
        ],
        index=list("ABCD"),
        columns=list("ABCD"),
    )
    part = coessential_partners(corr, top_k=2, min_corr=0.3)
    assert part["A"] == ["B", "C"]  # top-2 by correlation, D dropped


def test_map_partners_to_universe_reverts_to_mouse_symbols():
    upper_partners = {"ABI1": ["NCKAP1", "ABI2"], "NCKAP1": ["ABI1"]}
    upper2mouse = {"ABI1": "Abi1", "NCKAP1": "Nckap1"}  # Abi2 not in universe
    mouse = map_partners_to_universe(upper_partners, upper2mouse)
    assert mouse == {"Abi1": ["Nckap1"], "Nckap1": ["Abi1"]}
    assert np.all(["Abi2" not in v for v in mouse.values()])  # off-universe dropped
