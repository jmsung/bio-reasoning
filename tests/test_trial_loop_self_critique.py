"""Offline tests for the self-critique pass, the critique knob, and the A/B report."""

from __future__ import annotations

from bio_reasoning.trial_loop.agent_variants import agent_variant_grid
from bio_reasoning.trial_loop.archive import compare_agentic_vs_prompt, render_agentic_vs_prompt
from bio_reasoning.trial_loop.loop import make_configurable_agent_row_predictor, with_self_critique
from bio_reasoning.trial_loop.types import TrialRecord, Variant


def test_with_self_critique_revises_the_initial_pair():
    base = lambda pert, gene, seed: (0.8, 0.1)  # noqa: E731
    seen = {}

    def critic(pert, gene, initial):
        seen["initial"] = initial
        up, down = initial
        return (down, up)  # flip, to prove the critic's output is returned

    fn = with_self_critique(base, critic)
    assert fn("Stat1", "Irf1", 0) == (0.1, 0.8)
    assert seen["initial"] == (0.8, 0.1)  # critic saw the base agent's first pass


def test_critique_knob_produces_both_on_and_off_variants():
    grid = agent_variant_grid(self_critique=(False, True))
    crit_on = [v for v in grid if v.self_critique]
    crit_off = [v for v in grid if not v.self_critique]
    assert crit_on and crit_off
    assert all(v.id.endswith("-crit") for v in crit_on)
    # default grid stays lean (critique off) unless asked
    assert all(not v.self_critique for v in agent_variant_grid())


def test_self_critique_is_part_of_the_agent_cache_key():
    # Same tools, different self_critique → the agent must be rebuilt, not shared.
    built: list[tuple] = []

    def agent_fn_for(variant: Variant):
        built.append((variant.tools, variant.self_critique))
        return lambda p, g, s: (0.5, 0.5)

    predictor = make_configurable_agent_row_predictor(agent_fn_for)
    rows = [{"pert": "P0", "gene": "G0"}]
    off = Variant(id="agent-go-s1", tools=("go_terms",), self_critique=False, seeds=(0,))
    on = Variant(id="agent-go-s1-crit", tools=("go_terms",), self_critique=True, seeds=(0,))
    predictor(rows, off, 0, lambda r: None)
    predictor(rows, on, 0, lambda r: None)
    predictor(rows, off, 0, lambda r: None)  # cached — no rebuild
    assert built == [(("go_terms",), False), (("go_terms",), True)]


def test_self_critique_round_trips_through_json():
    rec = TrialRecord(
        variant=Variant(id="agent-go-s1-crit", tools=("go_terms",), self_critique=True),
        metrics={"mean": 0.5},
    )
    restored = TrialRecord.from_json(rec.to_json())
    assert restored.variant.self_critique is True


def _rec(vid: str, tools, mean: float) -> TrialRecord:
    return TrialRecord(variant=Variant(id=vid, tools=tools), metrics={"mean": mean})


def test_compare_agentic_vs_prompt_reports_best_of_each_and_delta():
    history = [
        _rec("de-votes-nfs0-s3", None, 0.55),  # prompt-only (tools=None)
        _rec("agent-go-s1", ("go_terms",), 0.60),  # agentic
        _rec("agent-net-s1", ("string_partners",), 0.58),  # agentic
    ]
    cmp = compare_agentic_vs_prompt(history)
    assert cmp["prompt_best"].variant.id == "de-votes-nfs0-s3"
    assert cmp["agentic_best"].variant.id == "agent-go-s1"
    assert abs(cmp["delta"] - 0.05) < 1e-9


def test_compare_handles_a_missing_arm():
    only_prompt = [_rec("de-votes-nfs0-s3", None, 0.55)]
    cmp = compare_agentic_vs_prompt(only_prompt)
    assert cmp["agentic_best"] is None
    assert cmp["delta"] is None


def test_render_agentic_vs_prompt_names_both_arms_and_the_delta():
    history = [
        _rec("de-votes-nfs0-s3", None, 0.55),
        _rec("agent-go-s1", ("go_terms",), 0.60),
    ]
    out = render_agentic_vs_prompt(history)
    assert "agent-go-s1" in out and "de-votes-nfs0-s3" in out
    assert "0.05" in out or "+0.050" in out
