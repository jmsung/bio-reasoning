"""Trial-loop core: evaluate a Track A prompt-only Variant on the dual-OOD split.

The loop's fitness surface is the leak-free ``holdout_split`` val partition scored
with the official ``mean(AUROC_de, AUROC_dir)`` metric — the only honest gate for a
tuned/prompted predictor (a small or naive CV is a mirage; see
``mb/findings/track-strategy.md``). Inference is injected as ``infer_fn`` so the core
is deterministic and offline-testable; the CLI wires the real gpt-oss-120b caller.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np
import pandas as pd

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.trial_loop.types import TrialRecord, Variant
from mlgenx import format_prompt, parse_answer
from mlgenx.prompts import CELL_DESC

# infer_fn(prompts, seed) -> one raw text response per prompt.
InferFn = Callable[[Sequence[str], int], Sequence[str]]


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


def predict_variant(
    df: pd.DataFrame,
    variant: Variant,
    infer_fn: InferFn,
    seed: int = 0,
    pert_frac: float = 0.4,
    gene_frac: float = 0.4,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Run ``variant`` over the val partition; return ``(val_idx, up, down)``.

    Inference runs on val rows only (train rows would only add cost). Predictions
    are averaged across ``variant.seeds`` — the Track A multi-sample recipe that
    turns hard up/down calls into graded scores.
    """
    train_idx, val_idx = holdout_split(df, seed=seed, pert_frac=pert_frac, gene_frac=gene_frac)
    examples = sample_examples(df.iloc[train_idx], variant, seed)
    val_rows = df.iloc[val_idx].to_dict("records")
    prompts = [_format(str(r["pert"]), str(r["gene"]), variant, examples) for r in val_rows]

    if not prompts:
        empty = np.zeros(0, dtype=float)
        return val_idx, empty, empty

    per_seed = [
        np.array([parse_answer(t) for t in infer_fn(prompts, s)], dtype=float)
        for s in variant.seeds
    ]
    mean_pairs = np.stack(per_seed).mean(axis=0)
    return val_idx, mean_pairs[:, 0], mean_pairs[:, 1]


def run_variant(
    df: pd.DataFrame,
    variant: Variant,
    infer_fn: InferFn,
    seed: int = 0,
    pert_frac: float = 0.4,
    gene_frac: float = 0.4,
    **record_kwargs: object,
) -> TrialRecord:
    """Evaluate ``variant`` on the dual-OOD val split → a :class:`TrialRecord`."""
    val_idx, up, down = predict_variant(
        df, variant, infer_fn, seed=seed, pert_frac=pert_frac, gene_frac=gene_frac
    )
    labels = df.iloc[val_idx]["label"].to_numpy()
    metrics = evaluate(labels, up, down)
    metrics["n_val"] = int(len(val_idx))
    return TrialRecord(variant=variant, metrics=metrics, **record_kwargs)  # type: ignore[arg-type]
