"""Data types for the trial-loop: a Variant to try and the TrialRecord it yields."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Variant:
    """One Track A prompt-only configuration to evaluate.

    Attributes:
        id: Stable identifier used in trial logs and the archive.
        prompt_template: Optional custom template with ``{pert}``/``{gene}``/
            ``{cell_desc}`` placeholders. ``None`` → resolve ``prompt`` instead.
            Takes precedence over ``prompt`` when set (explicit-string override).
        prompt: Named prompt-wording variant from ``trial_loop.prompt_variants``.
            ``"default"`` → the mlgenx default prompt (zero-shot, or few-shot when
            ``n_few_shot`` > 0); other names inject a knowledge-worded template that
            still composes with few-shot. Ignored when ``prompt_template`` is set.
        n_few_shot: Number of few-shot exemplars, drawn from the TRAIN partition
            only (leak-free). Ignored when ``prompt_template`` is custom.
        retrieval: How exemplars are chosen. ``"random"`` (default) samples the
            train partition once; ``"go_category"`` retrieves, per query, train
            exemplars whose perturbation shares the query's GO functional category
            (relevance-selected few-shot). Ignored when ``n_few_shot == 0``.
        seeds: Sampling seeds; per-seed predictions are averaged into a graded
            score (the multi-sample / self-consistency recipe — its length is the
            sample count for both the Track A prompt and the Track B agent).
        tools: Track B agentic tool config — the subset of real-data tools the
            agent may call (see ``trial_loop.tools``). ``None`` → prompt-only
            (Track A); a tuple (possibly empty) marks an agentic variant, and its
            identity keys the per-config agent cache.
        self_critique: Track B agentic knob — when ``True`` the agent runs a
            second self-critique/verify pass over its first prediction. Inert for
            prompt-only (``tools is None``) variants; part of the agent cache key.
    """

    id: str
    prompt_template: str | None = None
    prompt: str = "default"
    n_few_shot: int = 0
    retrieval: str = "random"
    seeds: tuple[int, ...] = (42, 43, 44)
    tools: tuple[str, ...] | None = None
    self_critique: bool = False


@dataclass
class TrialRecord:
    """Result of evaluating one :class:`Variant` on the dual-OOD val split.

    ``metrics`` carries the shared Track A quantity ``{auroc_de, auroc_dir,
    mean, n_val}`` (see ``eval.track_a_score.evaluate``).
    """

    variant: Variant
    metrics: dict[str, float]
    cost_usd: float | None = None
    tokens: dict[str, float] | None = None
    trace_path: str | None = None
    reflection: str | None = None

    def to_json(self) -> str:
        """Serialize to a single JSON line (for ``trials.jsonl``)."""
        return json.dumps(asdict(self), sort_keys=True)

    @classmethod
    def from_json(cls, line: str) -> "TrialRecord":
        """Inverse of :meth:`to_json`."""
        d = json.loads(line)
        v = d.pop("variant")
        v["seeds"] = tuple(v["seeds"])
        if v.get("tools") is not None:
            v["tools"] = tuple(v["tools"])
        return cls(variant=Variant(**v), **d)
