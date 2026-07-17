"""Offline tests for the agentic tool-config variant space + per-variant wiring.

The agentic lane searches tool subsets (which real-data tools the agent may call)
and self-consistency sample counts. ``make_configurable_agent_row_predictor`` picks
the agent per ``Variant.tools`` and drives the SAME split/score harness, so it is
offline-testable with a fake agent.
"""

from __future__ import annotations

import pandas as pd

from bio_reasoning.trial_loop.agent_variants import (
    AGENT_TOOL_SUBSETS,
    agent_variant_grid,
    make_agent_proposer,
)
from bio_reasoning.trial_loop.loop import make_configurable_agent_row_predictor, run_variant
from bio_reasoning.trial_loop.ruled_out import is_ruled_out
from bio_reasoning.trial_loop.types import TrialRecord, Variant


def test_agent_grid_is_nonempty_and_tool_configured():
    grid = agent_variant_grid()
    assert len(grid) >= 4
    assert all(v.id.startswith("agent-") for v in grid)
    # every agentic variant names a (possibly empty) tool subset — never None (that's Track A)
    assert all(v.tools is not None for v in grid)
    assert all(not is_ruled_out(v.id) for v in grid)


def test_include_traxler_false_excludes_traxler_tool_configs():
    grid = agent_variant_grid(include_traxler=False)
    assert grid  # still non-empty
    assert all("traxler_direction" not in (v.tools or ()) for v in grid)
    # the default grid DOES offer a Traxler config (so the exclusion is meaningful)
    assert any("traxler_direction" in (v.tools or ()) for v in agent_variant_grid())


def test_subsets_registry_covers_the_real_tools():
    all_tools = {t for subset in AGENT_TOOL_SUBSETS.values() for t in subset}
    assert {"go_terms", "string_partners", "traxler_direction"} <= all_tools


def test_agent_proposer_skips_ruled_out():
    poisoned = [
        Variant(id="string-degree-de", tools=()),  # ruled out
        Variant(id="agent-go-s1", tools=("go_terms",)),
    ]
    proposer = make_agent_proposer(poisoned)
    emitted, history = [], []
    while (v := proposer("", history)) is not None:
        emitted.append(v)
        history.append(TrialRecord(variant=v, metrics={"mean": 0.5}))
    assert emitted
    assert all(not is_ruled_out(v.id) for v in emitted)


def test_variant_tools_round_trips_through_json():
    v = Variant(id="agent-go-net-s3", tools=("go_terms", "string_partners"), seeds=(42, 43, 44))
    rec = TrialRecord(variant=v, metrics={"mean": 0.5})
    restored = TrialRecord.from_json(rec.to_json())
    assert restored.variant.tools == ("go_terms", "string_partners")
    assert isinstance(restored.variant.tools, tuple)


def test_track_a_variant_tools_default_none_round_trips():
    # A prompt-only (Track A) variant keeps tools=None through serialization.
    rec = TrialRecord(variant=Variant(id="de-votes-nfs0-s3"), metrics={"mean": 0.5})
    assert TrialRecord.from_json(rec.to_json()).variant.tools is None


def test_configurable_predictor_selects_agent_per_tool_config_and_scores():
    # A labelled mix (up/down/none) so both AUROC_de and AUROC_dir are defined; a
    # perfect fake agent then scores mean 1.0. frac=1.0 → every row lands in val.
    df = pd.DataFrame(
        {
            "pert": ["up0", "up1", "down0", "down1", "none0", "none1"],
            "gene": [f"G{i}" for i in range(6)],
            "label": ["up", "up", "down", "down", "none", "none"],
        }
    )
    built: list[tuple[str, ...]] = []

    def agent_fn_for(variant: Variant):
        built.append(variant.tools or ())

        def agent_fn(pert: str, gene: str, seed: int) -> tuple[float, float]:
            if pert.startswith("up"):
                return (0.9, 0.05)
            if pert.startswith("down"):
                return (0.05, 0.9)
            return (0.02, 0.02)  # none → low DE score

        return agent_fn

    predictor = make_configurable_agent_row_predictor(agent_fn_for)
    variant = Variant(id="agent-go-s1", tools=("go_terms",), seeds=(0,))
    rec = run_variant(df, variant, predictor, seed=0, pert_frac=1.0, gene_frac=1.0)
    assert rec.metrics["mean"] == 1.0
    # agent built exactly once for this single tool-config (cached across rows/seeds)
    assert built == [("go_terms",)]
