"""Preflight verification for the self-improvement loop — assert a real, healthy trial.

Codifies the hard-won loop deadlock / throughput-verification lesson:
*liveness ≠ working*. Twice the loop was called "verified" off connection /
socket-count health while calls were silently failing — an auth-401 that returned empty
responses, and an empty-eval that archived a degenerate nan-mean "win". So a preflight
trusts the loop only when it produces response **content** AND a trial **archives** with a
real (non-nan) mean over a **non-empty** val. Any degenerate mode fails loud.

Pure and offline-testable: :func:`run_preflight` takes any ``infer_fn`` (real OpenRouter
or a fake), so every degenerate mode is reproducible in a unit test.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from pathlib import Path

from bio_reasoning.trial_loop.archive import archive
from bio_reasoning.trial_loop.loop import make_prompt_row_predictor, run_variant
from bio_reasoning.trial_loop.types import TrialRecord, Variant

# infer_fn(prompts, seed) -> responses; the DE lane's OpenRouter completion signature.
InferFn = Callable[[Sequence[str], int], Sequence[str]]

_ARCHIVE_FILES = ("leaderboard.md", "best_variant.json")


class PreflightError(AssertionError):
    """A preflight assertion failed — the loop is NOT healthy, do not run unattended."""


class _NonEmptyCounter:
    """Wrap an ``infer_fn`` to tally non-empty responses (the auth-401 tripwire)."""

    def __init__(self, infer_fn: InferFn) -> None:
        self._infer_fn = infer_fn
        self.nonempty = 0
        self.total = 0

    def __call__(self, prompts: Sequence[str], seed: int) -> Sequence[str]:
        out = self._infer_fn(prompts, seed)
        for r in out:
            self.total += 1
            if r and str(r).strip():
                self.nonempty += 1
        return out


def assert_healthy(record: TrialRecord, output_dir: Path, nonempty_responses: int) -> None:
    """Raise :class:`PreflightError` unless the smoke trial is genuinely healthy.

    Checks, in order — each is a real failure mode that once passed as "verified":
    non-empty response content, a non-empty eval (``n_val > 0``), a real (non-nan)
    ``mean``, and a written archive. Liveness/connection metrics are deliberately NOT
    accepted as evidence.
    """
    if nonempty_responses <= 0:
        raise PreflightError(
            "all inference responses were empty — the model returned no content "
            "(auth-401 / dead endpoint?). Liveness ≠ working."
        )
    n_val = int(record.metrics.get("n_val", 0))
    if n_val <= 0:
        raise PreflightError(f"empty eval: n_val={n_val} — the smoke scored zero rows.")
    mean = float(record.metrics.get("mean", float("nan")))
    if math.isnan(mean):
        raise PreflightError("degenerate trial: mean is nan — no real score was produced.")
    for name in _ARCHIVE_FILES:
        if not (Path(output_dir) / name).is_file():
            raise PreflightError(f"no archive: {name} missing from {output_dir}.")


def run_preflight(
    df,
    infer_fn: InferFn,
    output_dir: Path,
    *,
    val_n: int = 80,
    baseline_id: str = "jsagent",
    seed: int = 0,
) -> TrialRecord:
    """Run one real (subsampled) smoke trial and assert it is healthy; return the record.

    Scores the ``baseline_id`` variant on the first ``val_n`` val rows (the DEV-ONLY
    subsample — minutes, not hours), archives it, then :func:`assert_healthy`. Raises
    :class:`PreflightError` on any degenerate mode (including the empty-eval that
    :func:`bio_reasoning.eval.track_a_score.evaluate` raises on). On success the loop is
    cleared to run unattended.
    """
    counter = _NonEmptyCounter(infer_fn)
    predictor = make_prompt_row_predictor(counter)
    variant = Variant(id=baseline_id, seeds=(42,))
    try:
        rec = run_variant(df, variant, predictor, seed=seed, val_n=val_n)
    except ValueError as e:  # evaluate() raises loud on an empty eval — surface it as preflight
        raise PreflightError(f"smoke trial failed to score: {e}") from e
    archive(output_dir, [rec])
    assert_healthy(rec, output_dir, counter.nonempty)
    return rec
