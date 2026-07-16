"""Trial-loop core: evaluate a Variant on the dual-OOD split, track-agnostically.

The loop's fitness surface is the leak-free ``holdout_split`` val partition scored
with the official ``mean(AUROC_de, AUROC_dir)`` metric — the only honest gate for a
tuned/prompted/agentic predictor (a small or naive CV is a mirage; see
``mb/findings/track-strategy.md``).

The prediction step is injected as a :data:`RowPredictor` — ``(val_rows, variant,
seed, examples) -> [(up, down), ...]`` — so the same split/score/reflect/archive
harness drives **both tracks**: Track A via :func:`make_prompt_row_predictor`
(format → single call → parse) and Track B via :func:`make_agent_row_predictor`
(run the agent per row). Predictors are injected, so the core is offline-testable
with fakes; the CLI wires the real gpt-oss-120b caller / agent.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np
import pandas as pd

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.trial_loop.reflect import Proposer, reflect
from bio_reasoning.trial_loop.types import TrialRecord, Variant
from mlgenx import format_prompt, parse_answer
from mlgenx.prompts import CELL_DESC

# infer_fn(prompts, seed) -> one raw text response per prompt (Track A model call).
InferFn = Callable[[Sequence[str], int], Sequence[str]]
# agent_fn(pert, gene, seed) -> graded (up, down) for one row (Track B agent).
AgentFn = Callable[[str, str, int], "tuple[float, float]"]
# row_predictor(rows, variant, seed, examples) -> one (up, down) per row.
# `rows` are val-row dicts (pert/gene/label); `examples` are train-only few-shot exemplars.
RowPredictor = Callable[
    ["list[dict]", Variant, int, "list[dict[str, str]] | None"],
    "Sequence[tuple[float, float]]",
]


def sample_examples(
    train_df: pd.DataFrame, variant: Variant, seed: int
) -> list[dict[str, str]] | None:
    """Draw ``variant.n_few_shot`` few-shot exemplars from the TRAIN partition.

    Sampling only from train keeps the val fitness leak-free: ``holdout_split``
    guarantees train shares zero perts and zero genes with val, so no exemplar can
    reveal a val row. Deterministic given ``seed``. Returns ``None`` for zero-shot.
    """
    if variant.n_few_shot <= 0 or len(train_df) == 0:
        return None
    rng = np.random.default_rng(seed)
    n = min(variant.n_few_shot, len(train_df))
    idx = rng.choice(len(train_df), size=n, replace=False)
    rows = train_df.iloc[idx]
    return [
        {"pert": str(r["pert"]), "gene": str(r["gene"]), "label": str(r["label"])}
        for r in rows.to_dict("records")
    ]


def _format(pert: str, gene: str, variant: Variant, examples: list[dict[str, str]] | None) -> str:
    if variant.prompt_template is not None:
        return variant.prompt_template.format(pert=pert, gene=gene, cell_desc=CELL_DESC)
    return format_prompt(pert, gene, examples=examples)


def make_prompt_row_predictor(infer_fn: InferFn) -> RowPredictor:
    """Track A predictor: format each row's prompt, call the model, parse to (up, down)."""

    def _predict(rows, variant, seed, examples):
        prompts = [_format(str(r["pert"]), str(r["gene"]), variant, examples) for r in rows]
        return [parse_answer(t) for t in infer_fn(prompts, seed)]

    return _predict


def make_agent_row_predictor(agent_fn: AgentFn) -> RowPredictor:
    """Track B predictor: run the agent per row → graded (up, down).

    ``examples`` are ignored — the agent gathers evidence via tools rather than
    few-shot exemplars.
    """

    def _predict(rows, variant, seed, examples):
        return [agent_fn(str(r["pert"]), str(r["gene"]), seed) for r in rows]

    return _predict


def predict_variant(
    df: pd.DataFrame,
    variant: Variant,
    row_predictor: RowPredictor,
    seed: int = 0,
    pert_frac: float = 0.4,
    gene_frac: float = 0.4,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Run ``variant`` over the val partition; return ``(val_idx, up, down)``.

    Prediction runs on val rows only (train rows would only add cost). Per-row
    predictions are averaged across ``variant.seeds`` — the multi-sample recipe that
    turns hard up/down calls into graded scores.
    """
    train_idx, val_idx = holdout_split(df, seed=seed, pert_frac=pert_frac, gene_frac=gene_frac)
    examples = sample_examples(df.iloc[train_idx], variant, seed)
    val_rows = df.iloc[val_idx].to_dict("records")

    if not val_rows:
        empty = np.zeros(0, dtype=float)
        return val_idx, empty, empty

    per_seed = [
        np.array(row_predictor(val_rows, variant, s, examples), dtype=float) for s in variant.seeds
    ]
    mean_pairs = np.stack(per_seed).mean(axis=0)
    return val_idx, mean_pairs[:, 0], mean_pairs[:, 1]


def run_variant(
    df: pd.DataFrame,
    variant: Variant,
    row_predictor: RowPredictor,
    seed: int = 0,
    pert_frac: float = 0.4,
    gene_frac: float = 0.4,
    **record_kwargs: object,
) -> TrialRecord:
    """Evaluate ``variant`` on the dual-OOD val split → a :class:`TrialRecord`."""
    val_idx, up, down = predict_variant(
        df, variant, row_predictor, seed=seed, pert_frac=pert_frac, gene_frac=gene_frac
    )
    labels = df.iloc[val_idx]["label"].to_numpy()
    metrics = evaluate(labels, up, down)
    metrics["n_val"] = int(len(val_idx))
    return TrialRecord(variant=variant, metrics=metrics, **record_kwargs)  # type: ignore[arg-type]


# on_trial(record, history_so_far) — persistence/side-effect hook per trial.
OnTrial = Callable[[TrialRecord, "list[TrialRecord]"], None]


def run_loop(
    df: pd.DataFrame,
    proposer: "Proposer",
    row_predictor: RowPredictor,
    seed: int = 0,
    pert_frac: float = 0.4,
    gene_frac: float = 0.4,
    max_trials: int | None = None,
    on_trial: OnTrial | None = None,
) -> list[TrialRecord]:
    """Drive ``propose → run_variant → reflect`` until the proposer converges.

    Each cycle: build the reflection from the history so far, ask ``proposer`` for
    the next :class:`Variant` (``None`` → converged, stop), evaluate it on the
    OOD-val split, append the record, and fire ``on_trial`` (persist/archive).
    Stops at ``max_trials`` if the proposer never converges. Returns the history.
    """
    history: list[TrialRecord] = []
    while max_trials is None or len(history) < max_trials:
        variant = proposer(reflect(history), history)
        if variant is None:
            break
        rec = run_variant(
            df, variant, row_predictor, seed=seed, pert_frac=pert_frac, gene_frac=gene_frac
        )
        history.append(rec)
        if on_trial is not None:
            on_trial(rec, history)
    return history
