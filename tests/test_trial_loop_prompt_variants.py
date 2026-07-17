"""Offline tests for the named prompt-wording registry + helpers."""

from __future__ import annotations

from bio_reasoning.trial_loop.prompt_variants import (
    PROMPT_VARIANTS,
    is_valid_prompt,
    render_examples_block,
)
from mlgenx.prompts import ANSWERS

_PLACEHOLDERS = ("{pert}", "{gene}", "{cell_desc}", "{examples_block}")


def test_default_is_the_mlgenx_sentinel():
    # "default" means "fall through to mlgenx.format_prompt" — represented as None.
    assert "default" in PROMPT_VARIANTS
    assert PROMPT_VARIANTS["default"] is None


def test_named_templates_carry_every_placeholder():
    named = {k: v for k, v in PROMPT_VARIANTS.items() if v is not None}
    assert named  # at least one knowledge-injected wording ships
    for name, tmpl in named.items():
        for ph in _PLACEHOLDERS:
            assert ph in tmpl, f"{name} missing {ph}"


def test_named_templates_format_without_error():
    for tmpl in PROMPT_VARIANTS.values():
        if tmpl is None:
            continue
        out = tmpl.format(pert="Aars", gene="Actb", cell_desc="ctx", examples_block="")
        assert "Aars" in out and "Actb" in out


def test_templates_do_not_hardcode_exemplar_answers():
    # Leak guard: a template must never bake in a concrete pair->label answer. The
    # only place an answer string may appear is via render_examples_block (train-only,
    # leak-free). So no mlgenx ANSWERS sentence may be present in a raw template.
    for name, tmpl in PROMPT_VARIANTS.items():
        if tmpl is None:
            continue
        for ans in ANSWERS.values():
            assert ans not in tmpl, f"{name} hardcodes an exemplar answer"


def test_is_valid_prompt():
    assert is_valid_prompt("default")
    assert all(is_valid_prompt(k) for k in PROMPT_VARIANTS)
    assert not is_valid_prompt("telepathy")
    assert not is_valid_prompt("")


def test_render_examples_block_empty():
    assert render_examples_block(None) == ""
    assert render_examples_block([]) == ""


def test_render_examples_block_renders_pairs_and_labels():
    exs = [
        {"pert": "X1", "gene": "Y1", "label": "up"},
        {"pert": "X2", "gene": "Y2", "label": "none"},
    ]
    block = render_examples_block(exs)
    assert "X1" in block and "Y1" in block
    assert "X2" in block and "Y2" in block
    assert ANSWERS["up"] in block and ANSWERS["none"] in block
    # trailing separator so the block slots cleanly before the Question line
    assert block.endswith("\n\n")
