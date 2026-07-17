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

import numpy as np

from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.trial_loop.loop import RowPredictor, run_variant
from bio_reasoning.trial_loop.types import Variant


def score_external_fold(
    fold_df,
    variant: Variant,
    row_predictor: RowPredictor,
    metric: str = "mean",
) -> float:
    """Score ``variant`` on a fixed external real-label fold (e.g. Traxler).

    Unlike the challenge splits there is no ``holdout_split`` — every fold row is
    predicted (averaged over ``variant.seeds``, the self-consistency recipe) and
    scored against the fold's own labels. Zero-shot: exemplars come from the
    challenge train, wired separately (Goal 3), so nothing here leaks the fold.
    """
    rows = fold_df.to_dict("records")
    per_seed = [
        np.array(row_predictor(rows, variant, s, lambda _r: None), dtype=float)
        for s in variant.seeds
    ]
    mean = np.stack(per_seed).mean(axis=0)
    return evaluate(fold_df["label"].to_numpy(), mean[:, 0], mean[:, 1])[metric]


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
    # External real-label fold (Traxler) — populated only for OOD-survivors; None
    # when no fold was supplied or the OOD gate already rejected the candidate.
    external_candidate: float | None = None
    external_baseline: float | None = None
    external_delta: float | None = None

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
    external_fold=None,
    external_margin: float = 0.0,
    **run_kwargs: object,
) -> GateResult:
    """Accept ``candidate`` iff it beats ``baseline`` on **all** ``seeds`` by > band.

    ``noise_band`` defaults to the baseline's own seed-to-seed range (its measured
    noise floor on these splits). A candidate whose smallest per-seed margin exceeds
    that floor is trusted; anything within noise is rejected.

    When ``external_fold`` (a real-label frame, e.g. Traxler) is given, an
    OOD-survivor must **also** beat the baseline on it by > ``external_margin`` —
    proving the challenge-OOD gain generalizes to held-out real labels rather than
    overfitting the challenge-train distribution. The fold is scored only for
    OOD-survivors (short-circuit) since each fold eval is expensive.
    """
    cand = score_across_seeds(df, candidate, row_predictor, seeds, metric, **run_kwargs)
    base = score_across_seeds(df, baseline, row_predictor, seeds, metric, **run_kwargs)
    if noise_band is None:
        noise_band = measure_noise_band(base)
    margins = [c - b for c, b in zip(cand, base, strict=True)]
    accepted = all(m > noise_band for m in margins)

    ext_cand = ext_base = ext_delta = None
    if external_fold is not None and accepted:
        ext_cand = score_external_fold(external_fold, candidate, row_predictor, metric)
        ext_base = score_external_fold(external_fold, baseline, row_predictor, metric)
        ext_delta = ext_cand - ext_base
        accepted = ext_delta > external_margin
    return GateResult(
        accepted,
        cand,
        base,
        margins,
        float(noise_band),
        metric,
        external_candidate=ext_cand,
        external_baseline=ext_base,
        external_delta=ext_delta,
    )
