"""Offline tests for the trial-loop core (no network; injected infer_fn)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.trial_loop.loop import predict_variant, run_variant, sample_examples
from bio_reasoning.trial_loop.types import TrialRecord, Variant

_UP, _DOWN, _NONE = "upregulated", "downregulated", "does not significantly affect"


def _frame(n: int = 120) -> pd.DataFrame:
    labels = ["up", "down", "none"]
    return pd.DataFrame(
        {
            "pert": [f"p{i % 30}" for i in range(n)],
            "gene": [f"g{i % 60}" for i in range(n)],
            "label": [labels[i % 3] for i in range(n)],
        }
    )


def _eq(a: float, b: float) -> bool:
    """nan-aware float equality."""
    return (math.isnan(a) and math.isnan(b)) or a == b


def test_run_variant_scores_val_rows_matching_evaluate() -> None:
    """run_variant scores exactly the val rows with the shared metric."""
    df = _frame()
    # pert_frac=gene_frac=1.0 → val = all rows (deterministic, multi-class).
    variant = Variant(id="v0", seeds=(1,))

    # Fake model: alternate up/down by prompt order (label-agnostic, deterministic).
    def fake(prompts, seed):
        return [_UP if i % 2 == 0 else _DOWN for i in range(len(prompts))]

    rec = run_variant(df, variant, fake, seed=0, pert_frac=1.0, gene_frac=1.0)

    val_labels = df["label"].to_numpy()
    up = np.array([1.0 if i % 2 == 0 else 0.0 for i in range(len(df))])
    down = np.array([0.0 if i % 2 == 0 else 1.0 for i in range(len(df))])
    exp = evaluate(val_labels, up, down)

    assert rec.metrics["n_val"] == len(df)
    for k in ("auroc_de", "auroc_dir", "mean"):
        assert _eq(rec.metrics[k], exp[k])
    assert not math.isnan(rec.metrics["mean"])  # non-degenerate here


def test_predict_variant_averages_across_seeds() -> None:
    """Multi-seed predictions are averaged element-wise (graded output)."""
    df = _frame()
    variant = Variant(id="v0", seeds=(1, 2))

    def fake(prompts, seed):
        ans = _UP if seed == 1 else _DOWN
        return [ans] * len(prompts)

    _, up, down = predict_variant(df, variant, fake, seed=0, pert_frac=1.0, gene_frac=1.0)
    # seed1 → (1,0), seed2 → (0,1); mean → (0.5, 0.5).
    assert np.allclose(up, 0.5)
    assert np.allclose(down, 0.5)


def test_sample_examples_leak_free() -> None:
    """Few-shot exemplars come only from the train partition — never val."""
    df = _frame()
    train_idx, val_idx = holdout_split(df, seed=0, pert_frac=0.4, gene_frac=0.4)
    assert len(val_idx) > 0 and len(train_idx) > 0
    variant = Variant(id="fs", n_few_shot=4)

    examples = sample_examples(df.iloc[train_idx], variant, seed=0)
    assert examples is not None and len(examples) == 4

    val_perts = set(df.iloc[val_idx]["pert"])
    val_genes = set(df.iloc[val_idx]["gene"])
    for ex in examples:
        assert ex["pert"] not in val_perts
        assert ex["gene"] not in val_genes


def test_trial_record_json_round_trip() -> None:
    """TrialRecord serializes to JSONL and back losslessly."""
    rec = TrialRecord(
        variant=Variant(id="v1", prompt_template="{pert} {gene}", n_few_shot=2, seeds=(42, 43)),
        metrics={"auroc_de": 0.51, "auroc_dir": 0.6, "mean": 0.555, "n_val": 200},
        cost_usd=0.12,
    )
    back = TrialRecord.from_json(rec.to_json())
    assert back == rec
    assert back.variant.seeds == (42, 43)
