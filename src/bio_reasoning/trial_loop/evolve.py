"""Population-based evolutionary driver — the AlphaEvolve loop over prompt templates.

The greedy :func:`bio_reasoning.trial_loop.driver.self_improve_loop` walks *one*
running-best baseline; AlphaEvolve instead maintains a **population** and lets
selection do the work. Each generation: rank the population by mean OOD-val score,
take the **top-K parents**, mutate each into **M children** via
:func:`bio_reasoning.trial_loop.prompt_mutation.mutate_prompt` (an injected LLM authors
a free-form edit; a per-child diversity hint keeps siblings distinct), evaluate every
child on the same dual-OOD split machinery the gate uses, then keep the **top-K of
parents ∪ children** as the next generation. Because parents compete for those slots,
selection is **elitist** — the best individual is never dropped, so best-so-far is
monotone non-decreasing.

Stops on the first of: ``max_generations``, a spend cap (``budget`` vs ``spent_fn``),
or ``dry`` — K consecutive generations whose best-so-far gain stays inside the noise
band (the diminishing-returns signal). Every evaluated child is emitted as a
:class:`TrialRecord` (carrying the parent Δ and the measured ``band=`` in its
reflection) so the journal hook auto-writes the whole trajectory.

Pure and file-free: ``propose_fn`` and ``row_predictor`` are injected, so the loop is
offline-testable with fakes; the runner wires the gpt-oss mutation author + the prompt
row-predictor around it.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from bio_reasoning.trial_loop.gate import measure_noise_band, score_across_seeds_full
from bio_reasoning.trial_loop.loop import ExampleKeyFn, RowPredictor
from bio_reasoning.trial_loop.prompt_mutation import MutateFn, mutate_prompt
from bio_reasoning.trial_loop.types import TrialRecord, Variant


@dataclass
class Individual:
    """One evaluated member of the population.

    ``scores`` are the per-split-seed metric values; ``mean`` is their average (the
    selection key); ``band`` is the seed-to-seed spread (this config's measured noise
    floor); ``metrics`` is the representative diagnostic row (n_val / both AUROCs / mean).
    """

    variant: Variant
    scores: list[float]
    mean: float
    band: float
    metrics: dict[str, float]


@dataclass
class EvolveResult:
    """Outcome of an evolutionary run."""

    population: list[Individual]  # final generation, best-first
    best: Individual
    records: list[TrialRecord] = field(default_factory=list)
    best_trajectory: list[float] = field(default_factory=list)  # best-so-far per generation
    generations: int = 0
    stopped_reason: str = "max_generations"
    spent: float = 0.0


def _mean(xs: Sequence[float]) -> float:
    return float(sum(xs) / len(xs)) if xs else float("nan")


def _rank_key(ind: Individual) -> float:
    """Selection key: mean, with nan ranked last so a failed eval never wins a slot."""
    return -math.inf if math.isnan(ind.mean) else ind.mean


def _representative(per_seed: list[dict[str, float]]) -> dict[str, float]:
    """Collapse per-split metric dicts into one diagnostic row (n_val from the first
    split; AUROCs/mean averaged, nan-skipping) so records carry real numbers."""
    out: dict[str, float] = {"n_val": per_seed[0].get("n_val", 0) if per_seed else 0}
    for k in ("auroc_de", "auroc_dir", "mean"):
        vals = [m[k] for m in per_seed if k in m and not math.isnan(m[k])]
        out[k] = float(sum(vals) / len(vals)) if vals else float("nan")
    return out


def _diversified(propose_fn: MutateFn, child_index: int) -> MutateFn:
    """Wrap ``propose_fn`` with a per-child variation hint so siblings differ.

    ``mutate_prompt`` calls ``propose_fn(instruction)``; appending a distinct hint per
    child index is the diversity knob — the LLM is asked for a *different* rewording each
    time rather than the same greedy edit, giving the population breadth to select from.
    """
    hint = (
        f"\n\n# Variation {child_index}: produce a DISTINCT rewording — a different "
        "angle from any other variation, not a near-copy."
    )
    return lambda instruction: propose_fn(instruction + hint)


def _evaluate(
    df,
    variant: Variant,
    row_predictor: RowPredictor,
    seeds: Sequence[int],
    metric: str,
    run_kwargs: dict[str, object],
) -> Individual:
    """Score ``variant`` once across the split ``seeds`` (the gate's per-seed machinery)."""
    per_seed = score_across_seeds_full(df, variant, row_predictor, seeds, **run_kwargs)
    scores = [m[metric] for m in per_seed]
    return Individual(
        variant=variant,
        scores=scores,
        mean=_mean(scores),
        band=measure_noise_band(scores),
        metrics=_representative(per_seed),
    )


def _record(child: Individual, parent: Individual, band_ref: float, generation: int) -> TrialRecord:
    """Build the child's TrialRecord — parent Δ + ``band=`` so the journal reads it back."""
    delta = child.mean - parent.mean
    accepted = not math.isnan(child.mean) and delta > band_ref
    return TrialRecord(
        variant=child.variant,
        metrics={
            "mean": child.mean,
            "baseline_mean": parent.mean,
            "min_margin": delta,
            "feasibility_ratio": (delta / band_ref) if band_ref > 0 else float("inf"),
            "accepted": float(accepted),
            "n_val": child.metrics.get("n_val", 0),
            "auroc_de": child.metrics.get("auroc_de", float("nan")),
            "auroc_dir": child.metrics.get("auroc_dir", float("nan")),
        },
        reflection=(
            f"gen {generation} parent={parent.variant.id}: "
            f"Δ={delta:+.3f} band={band_ref:.3f} accepted={accepted}"
        ),
    )


def _seed_record(ind: Individual, generation: int = 0) -> TrialRecord:
    """A gen-0 seed's record — no parent, so Δ is 0 and its own spread is the band."""
    return TrialRecord(
        variant=ind.variant,
        metrics={
            "mean": ind.mean,
            "baseline_mean": ind.mean,
            "min_margin": 0.0,
            "feasibility_ratio": 0.0,
            "accepted": 0.0,
            "n_val": ind.metrics.get("n_val", 0),
            "auroc_de": ind.metrics.get("auroc_de", float("nan")),
            "auroc_dir": ind.metrics.get("auroc_dir", float("nan")),
        },
        reflection=f"gen {generation} seed={ind.variant.id}: band={ind.band:.3f} (initial)",
    )


def evolve_loop(
    df,
    seed_variants: Sequence[Variant],
    row_predictor: RowPredictor,
    propose_fn: MutateFn,
    *,
    top_k: int = 2,
    children_per_parent: int = 2,
    max_generations: int = 5,
    seeds: Sequence[int] = (0, 1, 2),
    metric: str = "mean",
    noise_band: float | None = None,
    dry_generations: int = 2,
    budget: float | None = None,
    spent_fn: Callable[[], float] | None = None,
    example_key_fn: ExampleKeyFn | None = None,
    val_n: int | None = None,
    on_record: Callable[[TrialRecord], None] | None = None,
) -> EvolveResult:
    """Run the population-based AlphaEvolve loop over prompt-template variants.

    ``seed_variants`` bootstrap generation 0 (each should carry a ``prompt_template`` —
    that is what mutation edits). Each generation mutates the ``top_k`` parents into
    ``children_per_parent`` offspring apiece, evaluates them, and keeps the ``top_k`` of
    parents ∪ children (elitist → best-so-far is monotone). ``noise_band`` (default: the
    parent's own seed spread) is the accept/dry threshold: a child "beats" its parent
    only by more than the band, and ``dry_generations`` flat generations (best-so-far
    gain ≤ band) stop the run. ``budget`` caps ``spent_fn()`` (checked before each child
    eval). ``example_key_fn``/``val_n`` are forwarded to the split machinery
    (``val_n`` is DEV-ONLY smoke — it makes the gate untrustworthy; never select off it).
    Every evaluated child (and each gen-0 seed) is emitted via ``on_record`` for the
    journal.
    """
    run_kwargs: dict[str, object] = {"example_key_fn": example_key_fn, "val_n": val_n}
    records: list[TrialRecord] = []

    def emit(rec: TrialRecord) -> None:
        records.append(rec)
        if on_record is not None:
            on_record(rec)

    # --- Generation 0: evaluate the seeds. ---
    population = [_evaluate(df, v, row_predictor, seeds, metric, run_kwargs) for v in seed_variants]
    for ind in population:
        emit(_seed_record(ind))
    population.sort(key=_rank_key, reverse=True)

    best_so_far = _rank_key(population[0])
    best_trajectory = [population[0].mean]
    dry = 0
    stopped_reason = "max_generations"
    generations = 0
    over_budget = False

    for generation in range(1, max_generations + 1):
        parents = population[:top_k]
        children: list[Individual] = []

        for parent in parents:
            if over_budget:
                break
            band_ref = parent.band if noise_band is None else noise_band
            for child_index in range(children_per_parent):
                if budget is not None and spent_fn is not None and spent_fn() >= budget:
                    over_budget = True
                    break
                child_variant = mutate_prompt(
                    parent.variant.prompt_template or "",
                    records,
                    _diversified(propose_fn, child_index),
                )
                child = _evaluate(df, child_variant, row_predictor, seeds, metric, run_kwargs)
                children.append(child)
                emit(_record(child, parent, band_ref, generation))

        # Elitist selection: parents compete with children for the top_k slots.
        population = sorted(parents + children, key=_rank_key, reverse=True)[:top_k]
        generations = generation

        prev_best = best_so_far
        best_so_far = _rank_key(population[0])
        best_trajectory.append(population[0].mean)

        if over_budget:
            stopped_reason = "budget"
            break

        band_for_dry = noise_band if noise_band is not None else population[0].band
        improvement = best_so_far - prev_best if math.isfinite(best_so_far) else 0.0
        if improvement <= band_for_dry:
            dry += 1
            if dry >= dry_generations:
                stopped_reason = "dry"
                break
        else:
            dry = 0

    best = max(population, key=_rank_key)
    return EvolveResult(
        population=population,
        best=best,
        records=records,
        best_trajectory=best_trajectory,
        generations=generations,
        stopped_reason=stopped_reason,
        spent=spent_fn() if spent_fn is not None else 0.0,
    )
