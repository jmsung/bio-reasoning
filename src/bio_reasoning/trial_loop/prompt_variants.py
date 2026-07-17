"""Named prompt-wording variants for the Track A prompt lane of the trial-loop.

The loop's other Track A knobs (few-shot count, retrieval, sample count) vary *how*
the prompt is assembled; this axis varies *what the instruction says*. Each entry is
a **named** template so a proposer can select and validate a wording exactly like
``retrieval`` — never a free-form model-emitted string (token-cap + leak-safe: the
Kaggle Track A rules bar a prompt that directly contains the expected outputs).

``PROMPT_VARIANTS`` maps name -> template. ``default`` is ``None``: a sentinel meaning
"use the mlgenx default" (:func:`mlgenx.format_prompt`), so zero-/few-shot behaviour is
unchanged when this axis is not exercised. Every non-default template carries
``{pert} {gene} {cell_desc} {examples_block}`` so a knowledge-injected wording still
renders few-shot exemplars (:func:`render_examples_block`) — the axis *composes* with
the retrieval knob instead of silently overriding it (the inert-knob trap the tool lane
avoids, ``agent_variants.py``).

Injected knowledge is grounded in the team EDA, never in a test label:
- ``direction_prior`` — housekeeping-knockdown skews targets up, immune-knockdown skews
  them down (``knowledge/wiki/findings/track-a-eda.md`` §4;
  ``findings/direction-transfers-de-doesnt.md``).
- ``go_context`` — name the perturbation's functional class and the target's function
  first, then reason over the interaction (``track-a-eda.md`` "Implications for modeling").
"""

from __future__ import annotations

from mlgenx.prompts import _EXAMPLE_BLOCK, ANSWERS

# Knockdown direction prior — the one signal that transfers across the dual-OOD split.
_DIRECTION_PRIOR = """You are an expert molecular biologist who studies how genes are related using Perturb-seq.

Context: {cell_desc}

Prior knowledge to apply (empirical tendencies observed across perturbations, not hard rules):
- Knocking down a HOUSEKEEPING / essential perturbation gene tends to UP-regulate its targets.
- Knocking down an IMMUNE / inflammatory perturbation gene tends to DOWN-regulate its targets.
- Whether a target responds at all is genuinely hard to predict; commit to up or down only
  when the perturbation's function gives a concrete reason, otherwise prefer no effect.

{examples_block}Question: If you knockdown {pert} using CRISPRi in mouse BMDMs, what is the effect on {gene}?

Your answer must be one of:
A) Knockdown of {pert} results in up-regulation of {gene}.
B) Knockdown of {pert} results in down-regulation of {gene}.
C) Knockdown of {pert} does not significantly affect {gene}.

Answer:"""

# Function-first reasoning scaffold — surface pert/target function before deciding.
_GO_CONTEXT = """You are an expert molecular biologist who studies how genes are related using Perturb-seq.

Context: {cell_desc}

Reason step by step before answering:
1. State the functional class of the perturbed gene {pert} (housekeeping/essential, immune/inflammatory, or other).
2. State the primary biological function of the target gene {gene}.
3. From that interaction, decide whether knockdown of {pert} plausibly affects {gene}, and if so in which direction.

{examples_block}Question: If you knockdown {pert} using CRISPRi in mouse BMDMs, what is the effect on {gene}?

Your answer must be one of:
A) Knockdown of {pert} results in up-regulation of {gene}.
B) Knockdown of {pert} results in down-regulation of {gene}.
C) Knockdown of {pert} does not significantly affect {gene}.

Answer:"""

# name -> template. ``None`` = the mlgenx default path (zero-/few-shot unchanged).
PROMPT_VARIANTS: dict[str, str | None] = {
    "default": None,
    "direction_prior": _DIRECTION_PRIOR,
    "go_context": _GO_CONTEXT,
}


def is_valid_prompt(name: str) -> bool:
    """True iff ``name`` is a known prompt-wording variant (proposer guard)."""
    return name in PROMPT_VARIANTS


def render_examples_block(examples: list[dict[str, str]] | None) -> str:
    """Render few-shot exemplars into the ``{examples_block}`` slot of a named template.

    Returns ``""`` for no exemplars (zero-shot). Otherwise joins one mlgenx example
    block per exemplar and appends a blank-line separator so the block slots cleanly
    before the Question line. Exemplars are train-only by construction (the loop's
    leak-free provider), so their answer strings are safe to show.
    """
    if not examples:
        return ""
    blocks = [
        _EXAMPLE_BLOCK.format(pert=e["pert"], gene=e["gene"], answer=ANSWERS[e["label"]])
        for e in examples
    ]
    return "\n\n".join(blocks) + "\n\n"
