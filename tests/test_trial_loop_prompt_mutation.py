"""Offline tests for the free-form prompt MUTATION operator + leak-safe validator.

No network: ``propose_fn`` is a fake returning (i) a valid mutation, (ii) a leaky
mutation, (iii) a malformed one. Asserts the validator catches each and that an
invalid mutation always falls back to the parent (the loop never crashes).
"""

from __future__ import annotations

import pytest

from bio_reasoning.trial_loop.prompt_mutation import (
    MAX_TEMPLATE_TOKENS,
    REQUIRED_PLACEHOLDERS,
    make_mutation_proposer,
    mutate_prompt,
    validate_prompt,
)
from bio_reasoning.trial_loop.prompt_variants import PROMPT_VARIANTS
from bio_reasoning.trial_loop.types import TrialRecord, Variant

# ── Fixtures: a valid parent + the three fake-LLM outputs ──────────────────

_VALID_MUTATION = """You are a careful molecular biologist reasoning about CRISPRi Perturb-seq.

Context: {cell_desc}

Before answering, weigh the perturbation's functional class and the target's role, and
commit to a direction only when the biology gives a concrete reason; otherwise prefer no effect.

{examples_block}Question: If you knockdown {pert} using CRISPRi in mouse BMDMs, what is the effect on {gene}?

Your answer must be one of:
A) Knockdown of {pert} results in up-regulation of {gene}.
B) Knockdown of {pert} results in down-regulation of {gene}.
C) Knockdown of {pert} does not significantly affect {gene}.

Answer:"""

# Leak: bakes a concrete verdict for a NAMED (pert, gene) pair — Kaggle bars this.
_LEAKY_MUTATION = _VALID_MUTATION.replace(
    "{examples_block}Question:",
    "Note: Knockdown of Aars results in up-regulation of Actb.\n\n{examples_block}Question:",
)

# Malformed: drops required placeholders, has a stray unknown slot, no A/B/C structure.
_MALFORMED_MUTATION = "Just say up or down for {pert} and {gene}. {unknown_slot}"

# A concrete parent to fall back to (the direction_prior wording).
_PARENT = PROMPT_VARIANTS["direction_prior"]
assert _PARENT is not None


# ── validate_prompt: each rule in isolation ────────────────────────────────


def test_valid_template_passes():
    ok, reason = validate_prompt(_VALID_MUTATION)
    assert ok, reason


def test_shipped_named_templates_pass():
    # The evolutionary parents (the hand-authored wordings) must themselves validate.
    for name, tmpl in PROMPT_VARIANTS.items():
        if tmpl is None:
            continue
        ok, reason = validate_prompt(tmpl)
        assert ok, f"{name}: {reason}"


@pytest.mark.parametrize("missing", REQUIRED_PLACEHOLDERS)
def test_missing_placeholder_rejected(missing):
    broken = _VALID_MUTATION.replace(missing, "REMOVED")
    ok, reason = validate_prompt(broken)
    assert not ok and "placeholder" in reason.lower()


def test_leaky_pair_verdict_rejected_up():
    ok, reason = validate_prompt(_LEAKY_MUTATION)
    assert not ok and "leak" in reason.lower()


def test_leaky_pair_verdict_rejected_none():
    leaky = _VALID_MUTATION.replace(
        "{examples_block}Question:",
        "Hint: Knockdown of Cebpb does not significantly affect Il6.\n\n{examples_block}Question:",
    )
    ok, reason = validate_prompt(leaky)
    assert not ok and "leak" in reason.lower()


def test_placeholder_bound_options_are_not_a_leak():
    # The A/B/C option lines use {pert}/{gene} — those are the sanctioned verdicts,
    # not a hardcoded named-pair answer, so they must NOT trip the leak rule.
    ok, _ = validate_prompt(_VALID_MUTATION)
    assert ok


def test_over_token_cap_rejected():
    bloated = _VALID_MUTATION.replace(
        "Context: {cell_desc}", "Context: {cell_desc}\n" + ("reason " * 4000)
    )
    ok, reason = validate_prompt(bloated)
    assert not ok and "token" in reason.lower()


def test_missing_abc_structure_rejected():
    # Keeps placeholders + renders, but strips the A/B/C answer options → unparseable.
    no_options = """Context: {cell_desc}
{examples_block}Question: knockdown {pert}, effect on {gene}? Reply in prose.
Answer:"""
    ok, reason = validate_prompt(no_options)
    assert not ok and ("structure" in reason.lower() or "option" in reason.lower())


def test_unrenderable_stray_placeholder_rejected():
    ok, reason = validate_prompt(_MALFORMED_MUTATION)
    assert not ok


# ── mutate_prompt: valid / leaky / malformed via a fake propose_fn ──────────


def _history() -> list[TrialRecord]:
    return [
        TrialRecord(variant=Variant(id="parent", prompt_template=_PARENT), metrics={"mean": 0.55})
    ]


def test_mutate_valid_returns_mutated_variant():
    v = mutate_prompt(_PARENT, _history(), propose_fn=lambda _p: _VALID_MUTATION)
    assert v.prompt_template == _VALID_MUTATION
    assert v.id.startswith("mut-") and "fallback" not in v.id


def test_mutate_valid_wrapped_in_code_fence_is_extracted():
    raw = f"Here is my improved prompt:\n```text\n{_VALID_MUTATION}\n```\nDone."
    v = mutate_prompt(_PARENT, _history(), propose_fn=lambda _p: raw)
    assert v.prompt_template == _VALID_MUTATION


def test_mutate_leaky_falls_back_to_parent():
    v = mutate_prompt(_PARENT, _history(), propose_fn=lambda _p: _LEAKY_MUTATION)
    assert v.prompt_template == _PARENT
    assert "fallback" in v.id


def test_mutate_malformed_falls_back_to_parent():
    v = mutate_prompt(_PARENT, _history(), propose_fn=lambda _p: _MALFORMED_MUTATION)
    assert v.prompt_template == _PARENT
    assert "fallback" in v.id


def test_mutate_never_crashes_on_propose_fn_exception():
    def boom(_p: str) -> str:
        raise RuntimeError("endpoint down")

    v = mutate_prompt(_PARENT, _history(), propose_fn=boom)
    assert v.prompt_template == _PARENT  # degrades to parent, no exception


def test_mutate_passes_history_and_parent_into_propose_fn():
    seen: dict[str, str] = {}

    def spy(prompt: str) -> str:
        seen["prompt"] = prompt
        return _VALID_MUTATION

    mutate_prompt(_PARENT, _history(), propose_fn=spy)
    assert _PARENT in seen["prompt"]  # parent shown to the author
    assert "mean=0.550" in seen["prompt"] or "0.55" in seen["prompt"]  # reward history shown


# ── make_mutation_proposer: composes with the Proposer seam ─────────────────


def test_proposer_has_proposer_signature_and_mutates():
    p = make_mutation_proposer(lambda _p: _VALID_MUTATION, seed_template=_PARENT)
    v = p("reflection", [])  # (reflection, history) -> Variant
    assert isinstance(v, Variant) and v.prompt_template == _VALID_MUTATION


def test_proposer_empty_history_uses_seed_as_parent_on_fallback():
    p = make_mutation_proposer(lambda _p: _LEAKY_MUTATION, seed_template=_PARENT)
    v = p("", [])
    assert v.prompt_template == _PARENT  # leaky rejected → seed parent


def test_proposer_mutates_the_running_best_template():
    best_tmpl = _VALID_MUTATION
    hist = [
        TrialRecord(variant=Variant(id="a", prompt_template=_PARENT), metrics={"mean": 0.50}),
        TrialRecord(variant=Variant(id="b", prompt_template=best_tmpl), metrics={"mean": 0.60}),
    ]
    seen: dict[str, str] = {}

    def spy(prompt: str) -> str:
        seen["prompt"] = prompt
        return _VALID_MUTATION

    p = make_mutation_proposer(spy, seed_template=_PARENT)
    p("", hist)
    assert best_tmpl in seen["prompt"]  # parent = best trial's template, not the seed


def test_cap_constant_is_positive():
    assert MAX_TEMPLATE_TOKENS > 0
