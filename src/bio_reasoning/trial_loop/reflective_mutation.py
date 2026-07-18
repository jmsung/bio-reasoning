"""GEPA/ACE-style REFLECTION-driven mutation — learn *why* the best is wrong, then fix it.

:func:`trial_loop.prompt_mutation.mutate_prompt` proposes a revision **blind** — it sees
only the reward history (per-variant means), never *which* rows the current best got
wrong. This module closes that gap. It first **collects the incumbent's misclassified
val rows** (:func:`collect_val_errors`), hands the LLM those concrete failure cases, and
asks it to **reflect on the failure pattern** and propose a *targeted, reasoned* revision
— extracting far more signal per expensive rollout than a blind reword (the GEPA insight,
the right fit for our expensive+noisy eval).

The revision may target **either axis**:

- **prompt** — a leak-safe prompt-template edit, gated by
  :func:`prompt_mutation.validate_prompt` (the exact same Kaggle-leak guard blind
  mutation uses); or
- **pipeline** — a structured :class:`PipelineConfig` over the existing rank-fusion
  (:mod:`bio_reasoning.models.fuse`): which DE/DIR channels to fuse, their weights, and
  feature toggles — chosen from a fixed, shipped vocabulary so a hallucinated channel is
  rejected, never fused.

The reflector's stated **reason** rides on the resulting :class:`Variant` (``.reason``)
so the journal logs the *why* per generation. Every failure path — malformed output, a
leaky prompt, an unknown channel, a raised exception — **degrades to the parent**, so a
bad reflection can never leak a label or crash the loop. Pure and file-free: the
``reflect_fn`` is injected, so the whole reflect → reasoned-mutation → validate path is
offline-testable with a fake.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace

import numpy as np

from bio_reasoning.trial_loop.loop import ExampleKeyFn, RowPredictor, predict_variant
from bio_reasoning.trial_loop.prompt_mutation import validate_prompt
from bio_reasoning.trial_loop.types import PipelineConfig, Variant

# reflect_fn(instruction) -> raw model text: a REASON line + a revised prompt or a config
# JSON. Same single-string-in / raw-string-out seam as the blind MutateFn, so the runner
# wires the identical gpt-oss completion caller and tests inject a fake.
ReflectFn = Callable[[str], str]

# The DE/DIR channels the rank-fusion (models.fuse) can actually combine, grounded in the
# shipped channel builders so the reflector may only pick a signal that exists.
# DE axis (features/*.py, scripts/family_retrieval_eval.py):
DE_CHANNELS = ("two_stage_char", "neighbor_retrieval", "family_retrieval", "external_perturbqa")
# DIR axis — the three gate-passing direction channels (eval.direction_channels.CHANNELS):
DIR_CHANNELS = ("GO-DIR", "neighbour-DIR", "embedding-DIR")
ALLOWED_CHANNELS = DE_CHANNELS + DIR_CHANNELS
# Optional feature toggles the channels may condition on (features/*.py).
ALLOWED_FEATURES = ("essentiality", "marginal_properties", "string_degree", "gene_embedding")

_FENCE_RE = re.compile(r"```(?:[\w-]+)?\n(.*?)```", re.DOTALL)
_REASON_RE = re.compile(r"REASON:\s*(.+)", re.IGNORECASE)
# Flat JSON objects only (config arrays hold no nested braces), so this never swallows a
# prompt's {pert}/{gene} placeholder braces into a bogus multi-line match.
_JSON_OBJ_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)


@dataclass(frozen=True)
class ValError:
    """One misclassified validation row fed to the reflector.

    ``predicted`` is the incumbent's hard call, ``true`` the gold label, and
    ``confidence`` the model's score for its (wrong) call — so the reflector can weight
    *confidently* wrong rows, the most informative failures.
    """

    pert: str
    gene: str
    predicted: str
    true: str
    confidence: float


def _hard_label(up: float, down: float, de_threshold: float = 0.5) -> tuple[str, float]:
    """Collapse a graded ``(up, down)`` pair into a hard label + its confidence.

    ``de = up + down`` is the differential-expression mass: below ``de_threshold`` the
    call is ``none`` (confidence ``1 - de``); otherwise it is the heavier direction
    (confidence = that direction's mass). Confidence is clamped to ``[0, 1]``.
    """
    de = up + down
    if de < de_threshold:
        return "none", float(min(1.0, max(0.0, 1.0 - de)))
    if up >= down:
        return "up", float(min(1.0, max(0.0, up)))
    return "down", float(min(1.0, max(0.0, down)))


def select_errors(
    rows: Sequence[dict],
    up: np.ndarray,
    down: np.ndarray,
    top_n: int = 20,
    rng: np.random.Generator | None = None,
) -> list[ValError]:
    """Pick the incumbent's misclassified rows — the reflector's evidence.

    A row is an error when its hard label (:func:`_hard_label`) disagrees with the gold
    ``label``. With ``rng`` the errors are sampled at random; otherwise the most
    *confidently* wrong are taken first (descending confidence). At most ``top_n``.
    """
    errors: list[ValError] = []
    ups = np.asarray(up, dtype=float)
    downs = np.asarray(down, dtype=float)
    for r, u, d in zip(rows, ups, downs, strict=True):
        predicted, conf = _hard_label(float(u), float(d))
        true = str(r["label"])
        if predicted != true:
            errors.append(ValError(str(r["pert"]), str(r["gene"]), predicted, true, conf))
    if not errors:
        return []
    if rng is not None:
        idx = rng.permutation(len(errors))[:top_n]
        return [errors[i] for i in idx]
    errors.sort(key=lambda e: e.confidence, reverse=True)
    return errors[:top_n]


def collect_val_errors(
    df,
    variant: Variant,
    row_predictor: RowPredictor,
    *,
    seed: int = 0,
    top_n: int = 20,
    pert_frac: float = 0.4,
    gene_frac: float = 0.4,
    example_key_fn: ExampleKeyFn | None = None,
    val_n: int | None = None,
    rng: np.random.Generator | None = None,
) -> list[ValError]:
    """Run ``variant`` over the OOD-val split and return its misclassified rows.

    Reuses the loop's :func:`predict_variant` (same leak-free ``holdout_split`` and
    self-consistency averaging the gate scores), then diffs each row's hard call against
    its gold label. ``seed`` selects one split; ``top_n``/``rng`` pick which errors to
    surface (see :func:`select_errors`).
    """
    val_idx, up, down = predict_variant(
        df,
        variant,
        row_predictor,
        seed=seed,
        pert_frac=pert_frac,
        gene_frac=gene_frac,
        example_key_fn=example_key_fn,
        val_n=val_n,
    )
    if len(val_idx) == 0:
        return []
    rows = df.iloc[val_idx].to_dict("records")
    return select_errors(rows, up, down, top_n=top_n, rng=rng)


def format_errors(errors: Sequence[ValError]) -> str:
    """Render the misclassified rows as the reflector's evidence block."""
    if not errors:
        return "(no misclassified validation rows captured)"
    return "\n".join(
        f"- knockdown {e.pert} -> {e.gene}: predicted {e.predicted} "
        f"(confidence {e.confidence:.2f}), TRUE {e.true}"
        for e in errors
    )


def validate_pipeline_config(
    cfg: PipelineConfig,
    allowed_channels: Sequence[str] = ALLOWED_CHANNELS,
    allowed_features: Sequence[str] = ALLOWED_FEATURES,
) -> tuple[bool, str]:
    """Return ``(ok, reason)`` for a candidate fusion config.

    Enforces: at least one channel; every channel from the shipped vocabulary (an
    unknown/hallucinated channel is rejected — the loop can never fuse a signal that does
    not exist); one finite, non-negative weight per channel with a positive sum (an
    all-zero weighting fuses nothing); every feature from the allowed set. ``reason`` is
    ``""`` when ``ok``.
    """
    if not cfg.channels:
        return False, "empty channels"
    unknown = [c for c in cfg.channels if c not in allowed_channels]
    if unknown:
        return False, f"unknown channel(s): {', '.join(unknown)}"
    if len(cfg.weights) != len(cfg.channels):
        return (
            False,
            f"weights/channels length mismatch ({len(cfg.weights)} vs {len(cfg.channels)})",
        )
    if any((not math.isfinite(w)) or w < 0 for w in cfg.weights):
        return False, "weights must be finite and non-negative"
    if sum(cfg.weights) <= 0:
        return False, "weights sum to zero (fuses nothing)"
    bad_feat = [f for f in cfg.features if f not in allowed_features]
    if bad_feat:
        return False, f"unknown feature(s): {', '.join(bad_feat)}"
    return True, ""


_REFLECTION_INSTRUCTION = """You improve a system that predicts how a CRISPRi knockdown of a
perturbation gene affects a target gene (up / down / no effect) in mouse BMDMs.

The CURRENT BEST configuration made the following MISCLASSIFICATIONS on held-out
validation rows. Reflect on WHY these went wrong — the common failure pattern — then
propose ONE targeted revision that would fix that pattern.

MISCLASSIFIED VALIDATION ROWS (current best got these wrong):
{errors}

You may revise EITHER of two targets:

(A) PROMPT — rewrite the parent prompt below to reason better. Keep the placeholders
    {{pert}} {{gene}} {{cell_desc}} {{examples_block}} and the A/B/C answer options
    exactly. Do NOT state the answer for any specific gene pair.

(B) PIPELINE — change which fusion channels/weights/features the pipeline uses. Choose
    channels only from: {channels}. Features only from: {features}.

Reply in this format:
REASON: <one sentence naming the failure pattern and your fix>
Then EITHER the full revised prompt, OR a single JSON object like
{{"target": "config", "channels": ["neighbor_retrieval", "GO-DIR"], "weights": [1.0, 0.5], "features": ["essentiality"]}}

PARENT PROMPT:
{parent}
"""


def _extract_reason(raw: str) -> str:
    """Pull the reflector's stated REASON line (empty string when absent)."""
    m = _REASON_RE.search(raw or "")
    return m.group(1).strip() if m else ""


def _extract_config(raw: str) -> dict | None:
    """Find a config-shaped JSON object (has ``channels``) in ``raw``, else ``None``."""
    for m in _JSON_OBJ_RE.findall(raw or ""):
        try:
            obj = json.loads(m)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(obj, dict) and "channels" in obj:
            return obj
    return None


def _extract_prompt(raw: str) -> str:
    """Pull the revised prompt from ``raw`` — a fenced block if present, else the text
    below the REASON line."""
    m = _FENCE_RE.search(raw or "")
    if m:
        return m.group(1).strip()
    text = raw or ""
    # Drop a leading REASON: line so it does not pollute the template body.
    return _REASON_RE.sub("", text, count=1).strip()


def _short_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def _config_from_obj(obj: dict) -> PipelineConfig:
    """Build a :class:`PipelineConfig` from parsed JSON (tuple-ising the arrays)."""
    channels = tuple(str(c) for c in obj.get("channels", ()))
    weights_raw = obj.get("weights")
    # Default to equal weights when the reflector names channels but omits weights.
    weights = (
        tuple(float(w) for w in weights_raw)
        if isinstance(weights_raw, list)
        else (1.0,) * len(channels)
    )
    features = tuple(str(f) for f in obj.get("features", ()) or ())
    return PipelineConfig(channels=channels, weights=weights, features=features)


def _fallback(parent: Variant, why: str) -> Variant:
    """Degrade to the parent config, tagging the reason so the journal shows the miss."""
    tag = f"[reflect degraded: {why}]"
    return replace(
        parent,
        id=f"reflect-fallback-{_short_hash((parent.prompt_template or parent.id) + why)}",
        reason=tag if not parent.reason else f"{tag} {parent.reason}",
    )


def reflect_and_mutate(
    current_best: Variant,
    val_errors: Sequence[ValError],
    reflect_fn: ReflectFn,
    *,
    allowed_channels: Sequence[str] = ALLOWED_CHANNELS,
    allowed_features: Sequence[str] = ALLOWED_FEATURES,
) -> Variant:
    """Reflect on ``current_best``'s failures, then propose a reasoned revision.

    ``reflect_fn`` is shown the misclassified ``val_errors`` and the parent prompt, and
    returns a REASON plus either a revised prompt or a fusion-config JSON. A prompt is
    gated by :func:`prompt_mutation.validate_prompt`; a config by
    :func:`validate_pipeline_config`. On success the returned :class:`Variant` carries the
    revision **and** the reflector's ``reason``; on ANY failure — malformed, leaky, an
    unknown channel, or a raised exception — it degrades to ``current_best`` (never crashes,
    never leaks).
    """
    try:
        instruction = _REFLECTION_INSTRUCTION.format(
            errors=format_errors(val_errors),
            channels=", ".join(allowed_channels),
            features=", ".join(allowed_features),
            parent=current_best.prompt_template or "(no parent template)",
        )
        raw = reflect_fn(instruction)
    except Exception:  # noqa: BLE001 — a reflector fault must never derail the loop
        return _fallback(current_best, "reflector raised")

    reason = _extract_reason(raw)

    # (B) PIPELINE target: a config-shaped JSON is an explicit config proposal.
    cfg_obj = _extract_config(raw)
    if cfg_obj is not None:
        try:
            cfg = _config_from_obj(cfg_obj)
        except (TypeError, ValueError):
            return _fallback(current_best, "config unparseable")
        ok, why = validate_pipeline_config(cfg, allowed_channels, allowed_features)
        if not ok:
            return _fallback(current_best, why)
        canonical = f"{cfg.channels}{cfg.weights}{cfg.features}"
        return replace(
            current_best,
            id=f"reflect-cfg-{_short_hash(canonical)}",
            reason=f"[config] {reason}" if reason else "[config] (no reason given)",
            pipeline_config=cfg,
        )

    # (A) PROMPT target: validate the revised template with the same leak guard.
    candidate = _extract_prompt(raw)
    ok, why = validate_prompt(candidate)
    if not ok:
        return _fallback(current_best, why)
    return replace(
        current_best,
        id=f"reflect-{_short_hash(candidate)}",
        prompt_template=candidate,
        reason=f"[prompt] {reason}" if reason else "[prompt] (no reason given)",
    )
