"""Offline tests for the real-data agent tool set (GO / STRING / Traxler-direction).

Every tool must return a *grounded* answer from real gene knowledge injected via a
:class:`ToolBackend` — not a stub — and be deterministic given the backend. The
Traxler-direction tool is droppable (``include_traxler=False``) so it can be excluded
when the Traxler fold is the eval, closing the leak.
"""

from __future__ import annotations

import pandas as pd

from bio_reasoning.trial_loop.tools import (
    ToolBackend,
    format_go_terms,
    format_string_partners,
    format_traxler_direction,
    make_tools,
    traxler_direction_lookup,
)


def _fake_backend() -> ToolBackend:
    go = {"Stat1": ["response to interferon-gamma", "innate immune response"], "Actb": []}
    partners = {"Stat1": {"Jak2", "Irf1", "Stat2"}, "Actb": set()}
    trax = {("Stat1", "Irf1"): "up", ("Stat1", "Actb"): "none"}
    return ToolBackend(
        go_terms=lambda g: go.get(g, []),
        string_partners=lambda g: sorted(partners.get(g, set())),
        traxler_direction=lambda p, gn: trax.get((p, gn)),
    )


def test_go_terms_tool_surfaces_real_terms_not_a_stub():
    tools = {t.__name__: t for t in make_tools(_fake_backend())}
    out = tools["go_terms"]("Stat1")
    assert "response to interferon-gamma" in out
    assert "innate immune response" in out
    assert "Stat1" in out


def test_go_terms_tool_reports_absence_for_uncovered_gene():
    tools = {t.__name__: t for t in make_tools(_fake_backend())}
    assert "No GO:BP terms" in tools["go_terms"]("Actb")


def test_string_partners_tool_surfaces_real_neighbours():
    tools = {t.__name__: t for t in make_tools(_fake_backend())}
    out = tools["string_partners"]("Stat1")
    assert "Jak2" in out and "Irf1" in out and "Stat2" in out


def test_traxler_direction_tool_returns_grounded_direction():
    tools = {t.__name__: t for t in make_tools(_fake_backend())}
    up = tools["traxler_direction"]("Stat1", "Irf1")
    assert "up-regulated" in up
    none = tools["traxler_direction"]("Stat1", "Actb")
    assert "not differentially expressed" in none
    miss = tools["traxler_direction"]("Stat1", "Unknown")
    assert "No Traxler" in miss


def test_include_traxler_false_drops_the_tool():
    names = {t.__name__ for t in make_tools(_fake_backend(), include_traxler=False)}
    assert "traxler_direction" not in names
    assert {"go_terms", "string_partners"} <= names


def test_every_tool_has_a_docstring_for_dspy():
    # DSPy derives the tool description from the docstring; a bare tool is unusable.
    for t in make_tools(_fake_backend()):
        assert t.__doc__ and t.__doc__.strip()


def test_traxler_direction_lookup_builds_from_labels_frame():
    df = pd.DataFrame(
        [("Stat1", "Irf1", "up"), ("Stat1", "Actb", "none")],
        columns=["pert", "gene", "label"],
    )
    fn = traxler_direction_lookup(df)
    assert fn("Stat1", "Irf1") == "up"
    assert fn("Stat1", "Actb") == "none"
    assert fn("Stat1", "Missing") is None


def test_format_helpers_are_pure_and_grounded():
    assert "term-a" in format_go_terms("G", ["term-a", "term-b"])
    assert "No GO:BP terms" in format_go_terms("G", [])
    assert "P1" in format_string_partners("G", ["P1", "P2"])
    assert "No STRING" in format_string_partners("G", [])
    assert "down-regulated" in format_traxler_direction("P", "G", "down")
    assert "No Traxler" in format_traxler_direction("P", "G", None)
