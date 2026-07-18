"""Offline tests for GEPA/ACE reflection-driven mutation (no network, fakes only).

These exercise the full reflect → reasoned-mutation → validate path for BOTH targets:
error collection reads the incumbent's misclassified rows; a fake ``reflect_fn`` reading
those rows produces (i) a valid prompt edit, (ii) a valid fusion-config change, each
carrying the reflector's stated reason; and every malformed / leaky / unknown-channel /
raised-exception path degrades to the parent without crashing. A final integration test
drives ``evolve_loop`` in reflection mode and asserts the journal logs the why.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from bio_reasoning.trial_loop.evolve import evolve_loop
from bio_reasoning.trial_loop.journal import append_journal_entry
from bio_reasoning.trial_loop.prompt_variants import PROMPT_VARIANTS
from bio_reasoning.trial_loop.reflective_mutation import (
    ALLOWED_CHANNELS,
    ValError,
    collect_val_errors,
    format_errors,
    reflect_and_mutate,
    select_errors,
    validate_pipeline_config,
)
from bio_reasoning.trial_loop.types import PipelineConfig, TrialRecord, Variant

# ── Fixtures ────────────────────────────────────────────────────────────────

_PARENT = PROMPT_VARIANTS["direction_prior"]
assert _PARENT is not None

_PRED = {"up": (1.0, 0.0), "down": (0.0, 1.0), "none": (0.0, 0.0)}

_VALID_PROMPT = """You are a careful molecular biologist reasoning about CRISPRi Perturb-seq.

Context: {cell_desc}

Weigh the perturbation's functional class and the target's role before committing.

{examples_block}Question: If you knockdown {pert} using CRISPRi in mouse BMDMs, what is the effect on {gene}?

Your answer must be one of:
A) Knockdown of {pert} results in up-regulation of {gene}.
B) Knockdown of {pert} results in down-regulation of {gene}.
C) Knockdown of {pert} does not significantly affect {gene}.

Answer:"""

# Leak: a hardcoded verdict for a NAMED pair — must be rejected → parent.
_LEAKY_PROMPT = _VALID_PROMPT.replace(
    "{examples_block}Question:",
    "Note: Knockdown of Aars results in up-regulation of Actb.\n\n{examples_block}Question:",
)

# Malformed: drops placeholders + A/B/C structure.
_MALFORMED_PROMPT = "Just say up or down for {pert} and {gene}. {unknown_slot}"


def _reason(txt: str) -> str:
    return f"REASON: {txt}\n"


def _prompt_reply(reason: str = "confident up/down on none rows — prefer no effect") -> str:
    return _reason(reason) + _VALID_PROMPT


def _config_reply(reason: str = "direction channel too weak — add neighbor + GO-DIR") -> str:
    return (
        _reason(reason) + '{"target": "config", "channels": ["neighbor_retrieval", "GO-DIR"], '
        '"weights": [1.0, 0.5], "features": ["essentiality"]}'
    )


def _errors() -> list[ValError]:
    return [
        ValError("Aars", "Actb", "up", "none", 0.9),
        ValError("Cebpb", "Il6", "down", "up", 0.8),
    ]


# ── Error collection: reads the incumbent's misclassified rows ───────────────


def test_select_errors_finds_misclassified_rows_only():
    rows = [
        {"pert": "a", "gene": "x", "label": "up"},  # pred up  → correct
        {"pert": "b", "gene": "y", "label": "none"},  # pred up  → WRONG
        {"pert": "c", "gene": "z", "label": "down"},  # pred down → correct
    ]
    up = np.array([1.0, 1.0, 0.0])
    down = np.array([0.0, 0.0, 1.0])
    errs = select_errors(rows, up, down)
    assert [e.pert for e in errs] == ["b"]
    assert errs[0].predicted == "up" and errs[0].true == "none"


def test_select_errors_ranks_confident_first_and_caps_top_n():
    rows = [
        {"pert": "lo", "gene": "g", "label": "down"},  # pred up, conf 0.6
        {"pert": "hi", "gene": "g", "label": "down"},  # pred up, conf 0.95
    ]
    up = np.array([0.6, 0.95])
    down = np.array([0.0, 0.0])
    errs = select_errors(rows, up, down, top_n=1)
    assert len(errs) == 1 and errs[0].pert == "hi"  # most-confidently-wrong first


def test_select_errors_random_sampling_with_rng():
    rows = [{"pert": f"p{i}", "gene": "g", "label": "none"} for i in range(10)]
    up = np.ones(10)
    down = np.zeros(10)  # all predicted "up" → all wrong
    errs = select_errors(rows, up, down, top_n=3, rng=np.random.default_rng(0))
    assert len(errs) == 3


def test_collect_val_errors_reuses_predictor(monkeypatch):
    df = pd.DataFrame(
        {
            "pert": [f"p{i % 20}" for i in range(120)],
            "gene": [f"g{i % 17}" for i in range(120)],
            "label": [["up", "down", "none"][i % 3] for i in range(120)],
        }
    )

    def always_up(rows, variant, seed, get_examples):
        return [(1.0, 0.0) for _ in rows]  # predicts up for everything

    errs = collect_val_errors(df, Variant(id="v"), always_up, seed=0, top_n=50)
    assert errs  # some rows are down/none → wrong
    assert all(e.predicted == "up" and e.true != "up" for e in errs)


# ── validate_pipeline_config ─────────────────────────────────────────────────


def test_valid_config_passes():
    ok, reason = validate_pipeline_config(
        PipelineConfig(channels=("neighbor_retrieval", "GO-DIR"), weights=(1.0, 0.5))
    )
    assert ok, reason


def test_unknown_channel_rejected():
    ok, reason = validate_pipeline_config(
        PipelineConfig(channels=("made_up_channel",), weights=(1.0,))
    )
    assert not ok and "unknown channel" in reason


def test_weight_length_mismatch_rejected():
    ok, reason = validate_pipeline_config(
        PipelineConfig(channels=("GO-DIR", "neighbour-DIR"), weights=(1.0,))
    )
    assert not ok and "length mismatch" in reason


def test_empty_channels_rejected():
    ok, reason = validate_pipeline_config(PipelineConfig(channels=(), weights=()))
    assert not ok and "empty" in reason


def test_all_zero_weights_rejected():
    ok, reason = validate_pipeline_config(PipelineConfig(channels=("GO-DIR",), weights=(0.0,)))
    assert not ok and "zero" in reason


def test_negative_weight_rejected():
    ok, reason = validate_pipeline_config(PipelineConfig(channels=("GO-DIR",), weights=(-1.0,)))
    assert not ok and "non-negative" in reason


def test_unknown_feature_rejected():
    ok, reason = validate_pipeline_config(
        PipelineConfig(channels=("GO-DIR",), weights=(1.0,), features=("bogus",))
    )
    assert not ok and "feature" in reason


# ── reflect_and_mutate: PROMPT target ────────────────────────────────────────


def test_reflect_prompt_path_returns_reasoned_edit():
    v = reflect_and_mutate(
        Variant(id="best", prompt_template=_PARENT),
        _errors(),
        reflect_fn=lambda _i: _prompt_reply(),
    )
    assert v.prompt_template == _VALID_PROMPT
    assert v.id.startswith("reflect-") and "fallback" not in v.id
    assert v.reason and v.reason.startswith("[prompt]")
    assert "prefer no effect" in v.reason  # the stated why is carried


def test_reflect_prompt_path_reads_the_error_cases():
    seen: dict[str, str] = {}

    def spy(instruction: str) -> str:
        seen["i"] = instruction
        return _prompt_reply()

    reflect_and_mutate(Variant(id="best", prompt_template=_PARENT), _errors(), reflect_fn=spy)
    # the misclassified pairs are literally in the reflector's instruction
    assert "Aars" in seen["i"] and "Actb" in seen["i"] and "TRUE none" in seen["i"]
    assert _PARENT in seen["i"]  # the parent prompt is shown for a prompt edit


# ── reflect_and_mutate: PIPELINE-CONFIG target ───────────────────────────────


def test_reflect_config_path_returns_reasoned_fusion_config():
    parent = Variant(id="best", prompt_template=_PARENT)
    v = reflect_and_mutate(parent, _errors(), reflect_fn=lambda _i: _config_reply())
    assert v.pipeline_config is not None
    assert v.pipeline_config.channels == ("neighbor_retrieval", "GO-DIR")
    assert v.pipeline_config.weights == (1.0, 0.5)
    assert v.pipeline_config.features == ("essentiality",)
    assert v.id.startswith("reflect-cfg-")
    assert v.reason and v.reason.startswith("[config]") and "neighbor" in v.reason
    # a config-only change inherits the parent's prompt (fusion changed, wording kept)
    assert v.prompt_template == _PARENT


def test_reflect_config_offered_in_the_instruction_vocabulary():
    seen: dict[str, str] = {}

    def spy(instruction: str) -> str:
        seen["i"] = instruction
        return _config_reply()

    reflect_and_mutate(Variant(id="best", prompt_template=_PARENT), _errors(), reflect_fn=spy)
    # the allowed channel vocabulary is offered to the reflector
    for ch in ALLOWED_CHANNELS:
        assert ch in seen["i"]


# ── Degradation: every failure path falls back to the parent ─────────────────


def test_reflect_leaky_prompt_degrades_to_parent():
    parent = Variant(id="best", prompt_template=_PARENT)
    v = reflect_and_mutate(parent, _errors(), reflect_fn=lambda _i: _reason("x") + _LEAKY_PROMPT)
    assert v.prompt_template == _PARENT and "fallback" in v.id
    assert "degraded" in (v.reason or "")


def test_reflect_malformed_prompt_degrades_to_parent():
    parent = Variant(id="best", prompt_template=_PARENT)
    v = reflect_and_mutate(
        parent, _errors(), reflect_fn=lambda _i: _reason("x") + _MALFORMED_PROMPT
    )
    assert v.prompt_template == _PARENT and "fallback" in v.id


def test_reflect_unknown_channel_config_degrades_to_parent():
    parent = Variant(id="best", prompt_template=_PARENT)
    bad = _reason("y") + '{"target":"config","channels":["nonexistent"],"weights":[1.0]}'
    v = reflect_and_mutate(parent, _errors(), reflect_fn=lambda _i: bad)
    assert v.pipeline_config is None and v.prompt_template == _PARENT and "fallback" in v.id


def test_reflect_bad_weights_config_degrades_to_parent():
    parent = Variant(id="best", prompt_template=_PARENT)
    bad = _reason("y") + '{"channels":["GO-DIR","neighbour-DIR"],"weights":[1.0]}'
    v = reflect_and_mutate(parent, _errors(), reflect_fn=lambda _i: bad)
    assert v.pipeline_config is None and "fallback" in v.id


def test_reflect_never_crashes_on_reflect_fn_exception():
    def boom(_i: str) -> str:
        raise RuntimeError("endpoint down")

    parent = Variant(id="best", prompt_template=_PARENT)
    v = reflect_and_mutate(parent, _errors(), reflect_fn=boom)
    assert v.prompt_template == _PARENT and "fallback" in v.id  # degrades, no exception


def test_config_without_explicit_weights_defaults_to_equal():
    parent = Variant(id="best", prompt_template=_PARENT)
    reply = _reason("z") + '{"channels":["GO-DIR","neighbour-DIR"]}'
    v = reflect_and_mutate(parent, _errors(), reflect_fn=lambda _i: reply)
    assert v.pipeline_config is not None and v.pipeline_config.weights == (1.0, 1.0)


def test_format_errors_handles_empty():
    assert "no misclassified" in format_errors([])


# ── Serialization round-trips the new Variant fields ─────────────────────────


def test_variant_with_config_round_trips_through_json():
    v = Variant(
        id="reflect-cfg-abc",
        prompt_template=_PARENT,
        reason="[config] add neighbor",
        pipeline_config=PipelineConfig(
            channels=("GO-DIR",), weights=(1.0,), features=("essentiality",)
        ),
    )
    rec = TrialRecord(variant=v, metrics={"mean": 0.6})
    back = TrialRecord.from_json(rec.to_json())
    assert back.variant.pipeline_config == v.pipeline_config
    assert back.variant.reason == v.reason


# ── Integration: evolve_loop in reflection mode logs the why ─────────────────

_SCORE_RE = re.compile(r"SCORE=([0-9.]+)")


def _frame(n: int = 300) -> pd.DataFrame:
    labels = ["up", "down", "none"]
    return pd.DataFrame(
        {
            "pert": [f"p{i % 40}" for i in range(n)],
            "gene": [f"g{i % 37}" for i in range(n)],
            "label": [labels[i % 3] for i in range(n)],
        }
    )


def _template(score: float) -> str:
    return (
        f"SCORE={score:.4f}\n"
        "Predict how a CRISPRi knockdown of {pert} affects {gene} in {cell_desc}.\n"
        "{examples_block}\n"
        "A) up-regulated\nB) down-regulated\nC) not significantly changed\n"
    )


def _stable_frac(pert: str, gene: str) -> float:
    return (abs(hash((pert, gene))) % 10_000) / 10_000.0


def _predictor(rows, variant, seed, get_examples):
    m = _SCORE_RE.search(variant.prompt_template or "")
    p = float(m.group(1)) if m else 0.5
    return [
        _PRED[r["label"]] if _stable_frac(r["pert"], r["gene"]) < p else (0.0, 0.0) for r in rows
    ]


def _improving_reflect_fn():
    """A reflector that READS the errors, then returns a stronger reasoned prompt edit."""
    state = {"n": 0}

    def _fn(instruction: str) -> str:
        assert "MISCLASSIFIED VALIDATION ROWS" in instruction  # it was given the errors
        state["n"] += 1
        j = 0
        mv = re.search(r"# Variation (\d+)", instruction)
        if mv:
            j = int(mv.group(1))
        score = min(0.50 + 0.03 * state["n"] + 0.002 * j, 0.98)
        return _reason(f"gen fix #{state['n']}: sharpen direction call") + _template(score)

    return _fn


def test_evolve_reflection_mode_climbs_and_journal_logs_reason(tmp_path):
    path = tmp_path / "journal.md"
    history: list = []

    def on_record(rec) -> None:
        history.append(rec)
        append_journal_entry(path, history)

    res = evolve_loop(
        _frame(),
        [Variant(id="seed", prompt_template=_template(0.50), seeds=(42,))],
        _predictor,
        propose_fn=lambda _i: _template(0.50),  # unused in reflection mode
        top_k=2,
        children_per_parent=2,
        max_generations=3,
        seeds=(0, 1, 2),
        noise_band=0.0,
        reflect_fn=_improving_reflect_fn(),
        error_top_n=10,
        on_record=on_record,
    )
    # reflection-driven children were produced and the population climbed
    child_ids = {r.variant.id for r in res.records if r.variant.id != "seed"}
    assert any(cid.startswith("reflect-") for cid in child_ids)
    assert res.best_trajectory == sorted(res.best_trajectory)
    assert res.best_trajectory[-1] > res.best_trajectory[0]
    # the journal logs the reflector's stated reason per generation
    text = path.read_text()
    assert "reason:" in text and "sharpen direction call" in text
