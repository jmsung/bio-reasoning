"""Tests for the prompt-wording axis resolution in loop._format.

Precedence: explicit ``prompt_template`` (str) > named ``prompt`` (registry) >
default (mlgenx path). A named wording must COMPOSE with few-shot exemplars, not
override them silently.
"""

from __future__ import annotations

from bio_reasoning.trial_loop.loop import _format
from bio_reasoning.trial_loop.prompt_variants import render_examples_block
from bio_reasoning.trial_loop.types import Variant
from mlgenx import format_prompt

_EXS = [{"pert": "X1", "gene": "Y1", "label": "up"}]


def test_default_prompt_matches_mlgenx_zero_shot():
    v = Variant(id="d")  # prompt defaults to "default"
    assert _format("Aars", "Actb", v, None) == format_prompt("Aars", "Actb")


def test_default_prompt_matches_mlgenx_few_shot():
    v = Variant(id="d", n_few_shot=1)
    assert _format("Aars", "Actb", v, _EXS) == format_prompt("Aars", "Actb", examples=_EXS)


def test_named_prompt_injects_its_wording():
    v = Variant(id="dp", prompt="direction_prior")
    out = _format("Aars", "Actb", v, None)
    assert "HOUSEKEEPING" in out  # the injected direction prior
    assert "Aars" in out and "Actb" in out


def test_named_prompt_composes_with_few_shot():
    # nfs>0 + a named wording must render exemplars, not drop them (no inert knob).
    v = Variant(id="dp", prompt="direction_prior", n_few_shot=1)
    out = _format("Aars", "Actb", v, _EXS)
    assert "HOUSEKEEPING" in out
    assert render_examples_block(_EXS).strip() in out
    assert "X1" in out and "Y1" in out


def test_explicit_template_wins_over_named_prompt():
    v = Variant(id="t", prompt_template="{pert}|{gene}", prompt="direction_prior")
    assert _format("Aars", "Actb", v, None) == "Aars|Actb"
