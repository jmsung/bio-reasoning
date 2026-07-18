"""Free-form, LLM-authored prompt MUTATION operator + a leak-safe validator.

The named-wording axis (:mod:`trial_loop.prompt_variants`) only *selects* a fixed
template; the LLM proposer (:mod:`trial_loop.llm_proposer`) only picks a named one.
This module adds the missing evolutionary primitive: **mutation**. An injected LLM
(``propose_fn``) authors a free-form edit of a *parent* prompt template — rewording
the instruction to plausibly improve DE/direction reasoning, conditioned on the
reward history — and :func:`validate_prompt` gates it before it can reach the
evaluator. Anything unsafe or malformed falls back to the parent, so a hallucinated
mutation can never leak a label, blow the token budget, or crash the loop.

Leak rule (Kaggle Track A bars a prompt that directly contains a pair's expected
output): the A/B/C option lines are the only sanctioned verdicts and they MUST use
the ``{pert}``/``{gene}`` placeholders. A ``Knockdown of <X> results in
up/down-regulation of <Y>`` (or ``... does not significantly affect <Y>``) statement
whose slots are concrete gene names — not the placeholders — is a hardcoded
named-pair verdict and is rejected. General priors ("knocking down housekeeping genes
tends to up-regulate their targets") reference no specific pair and pass.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable

from bio_reasoning.trial_loop.reflect import Proposer, best_trial, reflect
from bio_reasoning.trial_loop.types import TrialRecord, Variant

# Every mutated template must keep these — the axis composes with retrieval/few-shot
# (``{examples_block}``) and cell context, exactly like the named templates.
REQUIRED_PLACEHOLDERS = ("{pert}", "{gene}", "{cell_desc}", "{examples_block}")

# Pre-render template cap. No project-wide *prompt* cap exists; we reuse the loop's
# per-call completion budget (``inference.make_openrouter_infer_fn`` max_tokens=512) as
# the reference so a runaway LLM-authored template is rejected. Estimated ~4 chars/token
# (the shipped named parents land ~290 est. tokens, comfortably under).
MAX_TEMPLATE_TOKENS = 512

# propose_fn(mutation_prompt) -> raw candidate template text (may wrap it in reasoning).
MutateFn = Callable[[str], str]

_FENCE_RE = re.compile(r"```(?:[\w-]+)?\n(.*?)```", re.DOTALL)

# A directional verdict bound to a concrete (non-placeholder) pair = a hardcoded label.
_LEAK_UP_DOWN_RE = re.compile(
    r"knockdown of\s+(\S+?)\s+results in\s+(?:up|down)-?regulation of\s+([^\s.]+)",
    re.IGNORECASE,
)
_LEAK_NONE_RE = re.compile(
    r"knockdown of\s+(\S+?)\s+does not significantly affect\s+([^\s.]+)",
    re.IGNORECASE,
)

_MUTATION_INSTRUCTION = """You improve an LLM prompt used to predict how a CRISPRi knockdown of a
perturbation gene affects a target gene (up / down / no effect) in mouse BMDMs.

Rewrite the PARENT PROMPT below to reason better about differential expression and
its direction. Keep the placeholders {{pert}} {{gene}} {{cell_desc}} {{examples_block}}
and the A/B/C answer options exactly. Do NOT state the answer for any specific gene
pair. Return only the new prompt.

REWARD HISTORY (variants tried and their OOD-val mean):
{history}

PARENT PROMPT:
{parent}
"""


def _estimate_tokens(text: str) -> int:
    """Cheap token estimate — max of ~4-chars/token and whitespace word count."""
    return max(len(text) // 4, len(text.split()))


def validate_prompt(template: str) -> tuple[bool, str]:
    """Return ``(ok, reason)`` for a candidate free-form prompt template.

    Enforces, in order: (c) token cap, (a) required placeholders, (d) parseability
    (renders cleanly with the placeholders), structure (A/B/C ternary options kept so
    :func:`mlgenx.parse_answer` can key on it), and (b) the no-hardcoded-verdict leak
    rule. ``reason`` is ``""`` when ``ok`` is ``True``.
    """
    if not template or not template.strip():
        return False, "empty template"

    if _estimate_tokens(template) > MAX_TEMPLATE_TOKENS:
        return False, f"over token cap ({_estimate_tokens(template)} > {MAX_TEMPLATE_TOKENS})"

    missing = [p for p in REQUIRED_PLACEHOLDERS if p not in template]
    if missing:
        return False, f"missing placeholder(s): {', '.join(missing)}"

    try:
        rendered = template.format(pert="Aars", gene="Actb", cell_desc="ctx", examples_block="")
    except (KeyError, IndexError, ValueError):
        return False, "template does not render cleanly (stray/unknown placeholder)"

    if not ("A)" in rendered and "B)" in rendered and "C)" in rendered):
        return False, "missing A/B/C answer-option structure (unparseable)"
    if not (
        re.search(r"up-?regulat", rendered, re.IGNORECASE)
        and re.search(r"down-?regulat", rendered, re.IGNORECASE)
        and re.search(r"not significantly|no significant", rendered, re.IGNORECASE)
    ):
        return False, "missing up/down/none verdicts — options not parseable"

    for pert_slot, tgt_slot in _LEAK_UP_DOWN_RE.findall(template) + _LEAK_NONE_RE.findall(template):
        if pert_slot != "{pert}" or tgt_slot != "{gene}":
            return False, f"leak: hardcoded verdict for named pair ({pert_slot}, {tgt_slot})"

    return True, ""


def _extract_template(raw: str) -> str:
    """Pull the template out of ``raw`` — a fenced code block if present, else the text."""
    m = _FENCE_RE.search(raw or "")
    return (m.group(1) if m else (raw or "")).strip()


def _short_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def mutate_prompt(
    parent_template: str,
    reward_history: list[TrialRecord],
    propose_fn: MutateFn,
) -> Variant:
    """Ask ``propose_fn`` to author a mutated prompt template; validate or fall back.

    ``propose_fn`` is shown the ``parent_template`` and a :func:`reflect` summary of
    ``reward_history`` (what's been tried + OOD-val means) and returns a candidate
    template. A candidate passing :func:`validate_prompt` yields a Variant carrying the
    free-form ``prompt_template``; on any failure — invalid, malformed, leaky, or a
    raised exception — the returned Variant carries the **parent** template instead, so
    the loop degrades gracefully and never crashes.
    """
    try:
        instruction = _MUTATION_INSTRUCTION.format(
            history=reflect(reward_history), parent=parent_template
        )
        candidate = _extract_template(propose_fn(instruction))
        ok, _reason = validate_prompt(candidate)
    except Exception:  # noqa: BLE001 — a proposer fault must never derail the loop
        ok, candidate = False, ""

    if ok:
        return Variant(id=f"mut-{_short_hash(candidate)}", prompt_template=candidate)
    return Variant(
        id=f"mut-fallback-{_short_hash(parent_template)}", prompt_template=parent_template
    )


def make_mutation_proposer(propose_fn: MutateFn, seed_template: str) -> Proposer:
    """Wrap :func:`mutate_prompt` as a ``Proposer`` (``(reflection, history) -> Variant``).

    The parent is the running-best trial's ``prompt_template`` (:func:`best_trial`), or
    ``seed_template`` when the history is empty or the best carries no template. Composes
    with the existing proposer seam without touching shared files — a runner can select
    it exactly like the grid/bandit/llm proposers.
    """

    def _propose(reflection: str, history: list[TrialRecord]) -> Variant | None:
        parent = seed_template
        if history:
            best = best_trial(history)
            if best.variant.prompt_template:
                parent = best.variant.prompt_template
        return mutate_prompt(parent, history, propose_fn)

    return _propose
