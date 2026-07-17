"""Goal 2: SUMMER-style neighbor-retrieval DE channel.

For an unseen (pert, gene), borrow the measured labels of TRAIN rows whose pert
is a neighbor of the query pert OR whose gene is a neighbor of the query gene,
and aggregate into a DE score (`s_de` = fraction differentially expressed) and a
direction score (`r` = P(up | DE)). Retrieval is TRAIN-only and never returns the
query's own pair — so it stays leak-free under the dual-OOD split.
"""

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from bio_reasoning.features.neighbor_retrieval import (
    build_neighbor_graph,
    fuse_neighbour_direction,
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


def test_build_neighbor_graph_restricts_to_train():
    partners = {"Q": {"Pa", "Pb", "Xz"}, "Gq": {"G1", "Gy"}}
    train = pd.DataFrame({"pert": ["Pa", "Pb"], "gene": ["G1", "G2"], "label": ["up", "none"]})
    queries = pd.DataFrame({"pert": ["Q"], "gene": ["Gq"]})
    pnb, gnb = build_neighbor_graph(queries, partners, train)
    assert pnb["Q"] == {"Pa", "Pb"}  # Xz (not a train pert) dropped
    assert gnb["Gq"] == {"G1"}  # Gy (not a train gene) dropped


def test_build_neighbor_graph_missing_symbol_is_empty():
    partners = {"Q": {"Pa"}}
    train = pd.DataFrame({"pert": ["Pa"], "gene": ["G1"], "label": ["up"]})
    queries = pd.DataFrame({"pert": ["Q"], "gene": ["Zz"]})
    pnb, gnb = build_neighbor_graph(queries, partners, train)
    assert pnb["Q"] == {"Pa"}
    assert gnb["Zz"] == set()  # symbol absent from partners → empty neighbour set


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


# --- Goal 1: track-agnostic neighbour-direction fusion helper -----------------


def test_fuse_neighbour_direction_preserves_de_ranking_and_reports_coverage():
    # Track-agnostic: fuse the neighbour direction into ANY base (up, down) — e.g. a
    # Track B floored submission. Only the base feeds the s_de bus and fuse()
    # rank-normalizes it, so the DE *ranking* (AUROC_de) is preserved while direction
    # gets the neighbour lift.
    train = _train()
    queries = pd.DataFrame({"pert": ["Q", "Zz"], "gene": ["Gq", "Yy"]})
    base_up = np.array([0.3, 0.1])
    base_down = np.array([0.2, 0.3])  # base DE = [0.5, 0.4] (distinct → real ranks)
    pert_nb = {"Q": {"Pa", "Pb"}}  # Q covered; Zz not
    gene_nb: dict[str, set] = {}
    fu, fd, covered = fuse_neighbour_direction(
        queries, base_up, base_down, train, pert_nb, gene_nb, min_support=1
    )
    assert fu.shape == fd.shape == (2,)
    # DE ranking preserved (fused DE = up+down is rank-monotonic with the base DE)
    assert np.array_equal(rankdata(fu + fd), rankdata(base_up + base_down))
    # per-row mask: Q covered via its neighbour, Zz not
    assert covered.tolist() == [True, False]
    assert covered.mean() == 0.5
    # valid graded simplex
    assert np.all(fu >= 0) and np.all(fd >= 0) and np.all(fu + fd <= 1 + 1e-9)


def test_fuse_neighbour_direction_no_coverage_falls_back_to_base_direction():
    train = _train()
    queries = pd.DataFrame({"pert": ["Zz", "Yy"], "gene": ["Aa", "Bb"]})  # no neighbours
    base_up = np.array([0.3, 0.1])
    base_down = np.array([0.2, 0.3])
    fu, fd, covered = fuse_neighbour_direction(
        queries, base_up, base_down, train, {}, {}, min_support=1
    )
    assert not covered.any()
    # with no neighbour cover, direction ranking == the base direction ranking
    base_r = base_up / (base_up + base_down)
    fused_r = fu / (fu + fd)
    assert np.array_equal(rankdata(fused_r), rankdata(base_r))
