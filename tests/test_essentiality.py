"""Goal 1: DepMap essentiality as a per-gene marginal responsiveness feature.

Essential/housekeeping genes are the broadly-responsive, transferable slice (see
knowledge/wiki/findings/housekeeping-transfer-hypothesis.md), so per-gene essentiality
is a leak-free marginal signal — unlike a train-derived DE rate. DepMap's continuous
gene-effect matrix is ~450 MB; its common-essential list + nonessential controls are
tiny, giving a robust ternary score (essential +1 / nonessential -1 / unknown 0),
keyed by human ortholog (UPPER(mouse symbol)).
"""

from bio_reasoning.features.essentiality import (
    parse_depmap_gene_list,
    ternary_essentiality,
)

_ESSENTIAL_FILE = "Gene\nADSL (158)\nAFG3L2 (10939)\nAK6\n"
_NONESSENTIAL_FILE = "Gene\nABCG8 (64241)\nADSL (158)\n"  # ADSL overlaps essential


def test_parse_strips_entrez_and_uppercases():
    syms = parse_depmap_gene_list("Gene\nAdsl (158)\nAfg3l2 (10939)\n")
    assert syms == {"ADSL", "AFG3L2"}


def test_parse_handles_no_entrez_and_blank_lines():
    syms = parse_depmap_gene_list(_ESSENTIAL_FILE + "\n   \n")
    assert syms == {"ADSL", "AFG3L2", "AK6"}


def test_ternary_essential_and_nonessential():
    m = ternary_essentiality(
        parse_depmap_gene_list(_ESSENTIAL_FILE),
        parse_depmap_gene_list(_NONESSENTIAL_FILE),
    )
    assert m["AFG3L2"] == 1.0  # common-essential
    assert m["ABCG8"] == -1.0  # nonessential control
    assert "UNKNOWNGENE" not in m  # unlisted → absent (looked up as 0.0 downstream)


def test_ternary_overlap_prefers_essential():
    m = ternary_essentiality(
        parse_depmap_gene_list(_ESSENTIAL_FILE),
        parse_depmap_gene_list(_NONESSENTIAL_FILE),
    )
    assert m["ADSL"] == 1.0  # in both sets → essential wins
