"""Self-improvement loop driver — propose → triple-verify → promote, until dry/budget.

The P9 loop shape: a cheap proposer walks the live DE-votes variant space, each
candidate is triple-verified against the running baseline, and only a survivor is
promoted (greedy). It stops on the first of: proposer exhausted (``converged``),
K consecutive non-improving rounds (``dry`` — P9's diminishing-returns signal via
the gate-feasibility ratio), a spend cap (``budget``), or ``max_trials``.

Pure and file-free so it is unit-testable; the runner script wires the OpenRouter
inference, the archive ledger, and the launchd/`claude -p` cadence around it.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from bio_reasoning.trial_loop.gate import triple_verify
from bio_reasoning.trial_loop.loop import ExampleKeyFn, RowPredictor
from bio_reasoning.trial_loop.reflect import Proposer, reflect
from bio_reasoning.trial_loop.types import TrialRecord, Variant


@dataclass
class SelfImproveResult:
    """Outcome of a loop run."""

    baseline: Variant  # final (possibly promoted) baseline
    accepted: list[Variant] = field(default_factory=list)
    records: list[TrialRecord] = field(default_factory=list)
    stopped_reason: str = "converged"
    spent: float = 0.0


def _mean(xs: Sequence[float]) -> float:
    return float(sum(xs) / len(xs)) if xs else float("nan")


def self_improve_loop(
    df,
    proposer: Proposer,
    row_predictor: RowPredictor,
    baseline: Variant,
    *,
    seeds: Sequence[int] = (0, 1, 2),
    metric: str = "mean",
    noise_band: float | None = None,
    dry_rounds: int = 2,
    budget: float | None = None,
    spent_fn: Callable[[], float] | None = None,
    max_trials: int | None = None,
    example_key_fn: ExampleKeyFn | None = None,
    external_fold=None,
    external_margin: float = 0.0,
    val_n: int | None = None,
    on_record: Callable[[TrialRecord], None] | None = None,
) -> SelfImproveResult:
    """Drive propose → triple-verify → promote until a stop condition trips.

    ``budget`` caps ``spent_fn()`` (e.g. cumulative tokens / USD); the check is at the
    top of each round, so at most one extra candidate is evaluated past the cap.
    ``noise_band`` is forwarded to :func:`triple_verify` (``None`` → measured from the
    baseline each round). A promoted baseline is compared against on subsequent rounds.
    ``example_key_fn`` supplies the relevance key for ``retrieval="go_category"``
    variants; without it those variants collapse to random few-shot (same exemplars).
    ``val_n`` (DEV-ONLY) truncates each split's val to its first N rows for a fast
    smoke — makes the gate UNtrustworthy, never promote off it (see
    :func:`bio_reasoning.trial_loop.loop.predict_variant`).
    """
    records: list[TrialRecord] = []
    accepted: list[Variant] = []
    history: list[TrialRecord] = []
    dry = 0
    reason = "converged"

    while True:
        if max_trials is not None and len(records) >= max_trials:
            reason = "max_trials"
            break
        if budget is not None and spent_fn is not None and spent_fn() >= budget:
            reason = "budget"
            break

        cand = proposer(reflect(history), history)
        if cand is None:
            reason = "converged"
            break

        gate = triple_verify(
            df,
            cand,
            baseline,
            row_predictor,
            seeds=seeds,
            metric=metric,
            noise_band=noise_band,
            external_fold=external_fold,
            external_margin=external_margin,
            example_key_fn=example_key_fn,
            val_n=val_n,
        )
        rec = TrialRecord(
            variant=cand,
            metrics={
                "mean": _mean(gate.candidate_scores),
                "baseline_mean": _mean(gate.baseline_scores),
                "min_margin": gate.min_margin,
                "feasibility_ratio": gate.feasibility_ratio,
                "accepted": float(gate.accepted),
            },
            reflection=(
                f"vs {baseline.id}: margins={[round(m, 3) for m in gate.margins]} "
                f"band={gate.noise_band:.3f} accepted={gate.accepted}"
                + (
                    f" | external Δ={gate.external_delta:+.3f} "
                    f"(cand {gate.external_candidate:.3f} vs base {gate.external_baseline:.3f})"
                    if gate.external_delta is not None
                    else ""
                )
            ),
        )
        records.append(rec)
        history.append(rec)
        if on_record is not None:
            on_record(rec)

        if gate.accepted:
            accepted.append(cand)
            baseline = cand  # greedy promote
            dry = 0
        else:
            dry += 1
            if dry >= dry_rounds:
                reason = "dry"
                break

    return SelfImproveResult(
        baseline=baseline,
        accepted=accepted,
        records=records,
        stopped_reason=reason,
        spent=spent_fn() if spent_fn is not None else 0.0,
    )
