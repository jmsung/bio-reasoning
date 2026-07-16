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
            ``{cell_desc}`` placeholders. ``None`` → the mlgenx default prompt
            (zero-shot, or few-shot when ``n_few_shot`` > 0).
        n_few_shot: Number of few-shot exemplars, drawn from the TRAIN partition
            only (leak-free). Ignored when ``prompt_template`` is custom.
        seeds: Sampling seeds; per-seed predictions are averaged into a graded
            score (the Track A multi-sample recipe).
    """

    id: str
    prompt_template: str | None = None
    n_few_shot: int = 0
    seeds: tuple[int, ...] = (42, 43, 44)


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
        return cls(variant=Variant(**v), **d)
