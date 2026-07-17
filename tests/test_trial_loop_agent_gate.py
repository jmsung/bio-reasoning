"""Offline: an agentic variant flows through the SAME triple-verify gate + Traxler fold.

Test Plan item 3 — the gate accepts an agentic candidate only if it beats the
prompt-only baseline on all seeds. The gate is predictor-agnostic, so we drive it
with a fake ``agent_fn_for`` whose agent quality depends on ``variant.tools`` (a
tool-using candidate vs a tool-free baseline).
"""

from __future__ import annotations

import pandas as pd

from bio_reasoning.trial_loop.gate import score_external_fold, triple_verify
from bio_reasoning.trial_loop.loop import make_configurable_agent_row_predictor
from bio_reasoning.trial_loop.types import Variant

# 6-row labelled mix; frac=1.0 → every row is val on every split seed (deterministic).
_DF = pd.DataFrame(
    {
        "pert": ["up0", "up1", "down0", "down1", "none0", "none1"],
        "gene": [f"G{i}" for i in range(6)],
        "label": ["up", "up", "down", "down", "none", "none"],
    }
)
_KW = dict(pert_frac=1.0, gene_frac=1.0)


def _perfect(pert: str, gene: str, seed: int) -> tuple[float, float]:
    if pert.startswith("up"):
        return (0.9, 0.05)
    if pert.startswith("down"):
        return (0.05, 0.9)
    return (0.02, 0.02)


def _uniform(pert: str, gene: str, seed: int) -> tuple[float, float]:
    return (0.5, 0.5)


def _predictor_where_tools_help():
    # tool-using variant (tools set) → perfect agent; tool-free baseline → uniform.
    def agent_fn_for(variant: Variant):
        return _perfect if variant.tools else _uniform

    return make_configurable_agent_row_predictor(agent_fn_for)


def test_gate_accepts_agentic_when_it_beats_prompt_baseline_on_all_seeds():
    predictor = _predictor_where_tools_help()
    candidate = Variant(id="agent-go-s1", tools=("go_terms",), seeds=(0,))
    baseline = Variant(id="prompt-only", tools=None, seeds=(0,))
    res = triple_verify(_DF, candidate, baseline, predictor, seeds=(0, 1, 2), **_KW)
    assert res.accepted
    assert all(m > 0 for m in res.margins)


def test_gate_rejects_agentic_within_noise():
    # Both arms use the uniform agent → candidate is no better than baseline.
    predictor = make_configurable_agent_row_predictor(lambda v: _uniform)
    candidate = Variant(id="agent-go-s1", tools=("go_terms",), seeds=(0,))
    baseline = Variant(id="prompt-only", tools=None, seeds=(0,))
    res = triple_verify(_DF, candidate, baseline, predictor, seeds=(0, 1, 2), **_KW)
    assert not res.accepted


def test_agentic_variant_scores_on_the_traxler_fold_leak_safe():
    # Traxler fold scored as a whole (no holdout); a leak-safe agentic variant that
    # does NOT name traxler_direction still produces a real [0,1] fold score.
    fold = pd.DataFrame(
        {
            "pert": ["up0", "down0", "none0", "up1"],
            "gene": ["G0", "G1", "G2", "G3"],
            "label": ["up", "down", "none", "up"],
        }
    )
    predictor = make_configurable_agent_row_predictor(lambda v: _perfect)
    variant = Variant(id="agent-go-net-s1", tools=("go_terms", "string_partners"), seeds=(0,))
    score = score_external_fold(fold, variant, predictor)
    assert 0.0 <= score <= 1.0
    assert score == 1.0  # the perfect agent nails the fold
