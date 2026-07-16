"""Goal 2: SUMMER-style neighbor-retrieval DE channel.

For an unseen (pert, gene), borrow the measured labels of TRAIN rows whose pert
is a neighbor of the query pert OR whose gene is a neighbor of the query gene,
and aggregate into a DE score (`s_de` = fraction differentially expressed) and a
direction score (`r` = P(up | DE)). Retrieval is TRAIN-only and never returns the
query's own pair — so it stays leak-free under the dual-OOD split.
"""

import numpy as np
import pandas as pd

from bio_reasoning.features.neighbor_retrieval import (
    neighbor_channel,
    retrieve_neighbor_labels,
)


def _train() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "pert": ["Pa", "Pa", "Pb", "Pc", "Pc", "Pd"],
            "gene": ["G1", "G2", "G1", "G3", "G4", "G4"],
            "label": ["up", "none", "up", "down", "none", "down"],
        }
    )


def test_retrieve_aggregates_neighbor_labels():
    train = _train()
    # query pert Q neighbors {Pa, Pb}; query gene Gq neighbors {} → retrieve Pa/Pb rows
    pert_nb = {"Q": {"Pa", "Pb"}}
    gene_nb = {"Gq": set()}
    s_de, r = retrieve_neighbor_labels("Q", "Gq", train, pert_nb, gene_nb)
    # retrieved: (Pa,G1,up),(Pa,G2,none),(Pb,G1,up) → 2/3 DE, both up → r=1.0
    assert s_de == 2 / 3
    assert r == 1.0


def test_retrieve_union_of_pert_and_gene_neighbors():
    train = _train()
    pert_nb = {"Q": {"Pd"}}  # (Pd,G4,down)
    gene_nb = {"Gq": {"G3"}}  # (Pc,G3,down)
    s_de, r = retrieve_neighbor_labels("Q", "Gq", train, pert_nb, gene_nb)
    # retrieved: (Pd,G4,down),(Pc,G3,down) → 2/2 DE, both down → r=0.0
    assert s_de == 1.0
    assert r == 0.0


def test_retrieve_excludes_query_own_pair():
    train = _train()
    # query (Pa, G1) IS a train row; neighbor set includes Pa — must not borrow its own label
    pert_nb = {"Pa": {"Pa"}}
    gene_nb = {"G1": {"G1"}}
    s_de, r = retrieve_neighbor_labels("Pa", "G1", train, pert_nb, gene_nb)
    # all Pa-rows and G1-rows EXCEPT (Pa,G1): (Pa,G2,none),(Pb,G1,up) → 1/2 DE
    assert s_de == 0.5


def test_retrieve_uncovered_returns_nan():
    train = _train()
    s_de, r = retrieve_neighbor_labels("Z", "Gz", train, {"Z": {"Nope"}}, {"Gz": set()})
    assert np.isnan(s_de) and np.isnan(r)


def test_retrieve_min_support_gates_thin_evidence():
    train = _train()
    pert_nb = {"Q": {"Pb"}}  # only (Pb,G1,up) → 1 row
    s_de, r = retrieve_neighbor_labels("Q", "Gq", train, pert_nb, {"Gq": set()}, min_support=2)
    assert np.isnan(s_de)


def test_neighbor_channel_builds_aligned_buses():
    train = _train()
    queries = pd.DataFrame({"pert": ["Q", "Z"], "gene": ["Gq", "Gz"]})
    pert_nb = {"Q": {"Pa"}, "Z": set()}
    gene_nb = {"Gq": set(), "Gz": set()}
    ch = neighbor_channel(queries, train, pert_nb, gene_nb)
    assert ch.name == "neighbor_retrieval"
    assert ch.s_de.shape == (2,) and ch.r.shape == (2,)
    assert np.isfinite(ch.s_de[0])  # Q covered via Pa
    assert np.isnan(ch.s_de[1])  # Z uncovered
