"""Triple-verify gate — the P9 anti-false-positive filter for the trial-loop.

P9's hard-won lesson: *your fast evaluator lies*. A single-split "improvement"
is often seed noise, and promoting it is catastrophic (our recurring +0.007 phantom
lifts). So a candidate is trusted only if it beats the baseline on **every** one of
several independent OOD splits by **more than the seed-to-seed noise band** — not
on a lucky average. Conservative by design: it prefers false negatives (miss a real
gain) over false positives (ship a phantom), exactly as P9 prescribes.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from bio_reasoning.trial_loop.loop import RowPredictor, run_variant
from bio_reasoning.trial_loop.types import Variant


def score_across_seeds(
    df,
    variant: Variant,
    row_predictor: RowPredictor,
    seeds: Sequence[int] = (0, 1, 2),
    metric: str = "mean",
    **run_kwargs: object,
) -> list[float]:
    """Score ``variant`` on each of ``seeds`` independent dual-OOD splits.

    ``seeds`` here are *split* seeds (each re-draws ``holdout_split``), distinct
    from ``variant.seeds`` (the multi-sample average within one split).
    """
    return [
        run_variant(df, variant, row_predictor, seed=s, **run_kwargs).metrics[metric]  # type: ignore[arg-type]
        for s in seeds
    ]


def measure_noise_band(scores: Sequence[float]) -> float:
    """Seed-to-seed spread of a fixed config = the observed range (max − min)."""
    return float(max(scores) - min(scores))


@dataclass
class GateResult:
    """Verdict of a triple-verify run. ``feasibility_ratio`` = P9's gate-feasibility
    (min margin / noise band) — Goal 4's loop-until-dry signal."""

    accepted: bool
    candidate_scores: list[float]
    baseline_scores: list[float]
    margins: list[float]
    noise_band: float
    metric: str

    @property
    def min_margin(self) -> float:
        return min(self.margins)

    @property
    def feasibility_ratio(self) -> float:
        return self.min_margin / self.noise_band if self.noise_band > 0 else float("inf")


def triple_verify(
    df,
    candidate: Variant,
    baseline: Variant,
    row_predictor: RowPredictor,
    seeds: Sequence[int] = (0, 1, 2),
    metric: str = "mean",
    noise_band: float | None = None,
    **run_kwargs: object,
) -> GateResult:
    """Accept ``candidate`` iff it beats ``baseline`` on **all** ``seeds`` by > band.

    ``noise_band`` defaults to the baseline's own seed-to-seed range (its measured
    noise floor on these splits). A candidate whose smallest per-seed margin exceeds
    that floor is trusted; anything within noise is rejected.
    """
    cand = score_across_seeds(df, candidate, row_predictor, seeds, metric, **run_kwargs)
    base = score_across_seeds(df, baseline, row_predictor, seeds, metric, **run_kwargs)
    if noise_band is None:
        noise_band = measure_noise_band(base)
    margins = [c - b for c, b in zip(cand, base, strict=True)]
    accepted = all(m > noise_band for m in margins)
    return GateResult(accepted, cand, base, margins, float(noise_band), metric)
