"""Offline tests for the trial-loop core (no network; injected row predictors)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from bio_reasoning.eval.split import holdout_split
from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.trial_loop.loop import (
    make_agent_row_predictor,
    make_prompt_row_predictor,
    predict_variant,
    run_loop,
    run_variant,
    sample_examples,
)
from bio_reasoning.trial_loop.reflect import make_grid_proposer
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

    rec = run_variant(
        df, variant, make_prompt_row_predictor(fake), seed=0, pert_frac=1.0, gene_frac=1.0
    )

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

    _, up, down = predict_variant(
        df, variant, make_prompt_row_predictor(fake), seed=0, pert_frac=1.0, gene_frac=1.0
    )
    # seed1 → (1,0), seed2 → (0,1); mean → (0.5, 0.5).
    assert np.allclose(up, 0.5)
    assert np.allclose(down, 0.5)


def test_predict_variant_val_n_subsamples_first_n_deterministic() -> None:
    """--val-n path: val is the first N holdout rows (deterministic), predictions match."""
    df = _frame()
    variant = Variant(id="v0", seeds=(1,))

    def fake(prompts, seed):
        return [_UP if i % 2 == 0 else _DOWN for i in range(len(prompts))]

    rp = make_prompt_row_predictor(fake)
    full_idx, _, _ = predict_variant(df, variant, rp, seed=0, pert_frac=1.0, gene_frac=1.0)
    assert len(full_idx) > 5  # full val is large; the subsample is a strict prefix

    sub_idx, up, down = predict_variant(
        df, variant, rp, seed=0, pert_frac=1.0, gene_frac=1.0, val_n=5
    )
    assert list(sub_idx) == list(full_idx[:5])
    assert len(up) == 5 and len(down) == 5


def test_run_variant_val_n_shrinks_n_val() -> None:
    """run_variant threads val_n → n_val reflects the subsample, not the full split."""
    df = _frame()
    variant = Variant(id="v0", seeds=(1,))

    def fake(prompts, seed):
        return [_UP] * len(prompts)

    rec = run_variant(
        df, variant, make_prompt_row_predictor(fake), seed=0, pert_frac=1.0, gene_frac=1.0, val_n=8
    )
    assert rec.metrics["n_val"] == 8


def test_val_n_none_is_full_val() -> None:
    """val_n=None (default) leaves the full holdout partition untouched — the real gate."""
    df = _frame()
    variant = Variant(id="v0", seeds=(1,))
    _, full_idx = holdout_split(df, seed=0, pert_frac=1.0, gene_frac=1.0)

    def fake(prompts, seed):
        return [_UP] * len(prompts)

    idx, _, _ = predict_variant(
        df, variant, make_prompt_row_predictor(fake), seed=0, pert_frac=1.0, gene_frac=1.0
    )
    assert list(idx) == list(full_idx)


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


def test_run_loop_drives_grid_to_convergence() -> None:
    """run_loop evaluates each candidate once then stops when the proposer converges."""
    df = _frame()
    cands = [Variant(id="v0", seeds=(1,)), Variant(id="v1", seeds=(1,))]

    persisted: list[str] = []

    def fake(prompts, seed):
        return [_UP] * len(prompts)

    hist = run_loop(
        df,
        make_grid_proposer(cands),
        make_prompt_row_predictor(fake),
        pert_frac=1.0,
        gene_frac=1.0,
        on_trial=lambda rec, h: persisted.append(rec.variant.id),
    )
    assert [r.variant.id for r in hist] == ["v0", "v1"]
    assert persisted == ["v0", "v1"]  # on_trial fired per trial
    assert all("mean" in r.metrics for r in hist)


def test_run_loop_respects_max_trials() -> None:
    """A never-converging proposer is bounded by max_trials."""
    df = _frame()

    def endless(reflection, history):
        return Variant(id=f"v{len(history)}", seeds=(1,))

    def fake(prompts, seed):
        return [_UP] * len(prompts)

    hist = run_loop(
        df, endless, make_prompt_row_predictor(fake), pert_frac=1.0, gene_frac=1.0, max_trials=3
    )
    assert [r.variant.id for r in hist] == ["v0", "v1", "v2"]


def test_agent_row_predictor_drives_same_loop() -> None:
    """A Track B-style agent_fn drives the identical scoring path (make_agent_row_predictor)."""
    df = _frame()
    variant = Variant(id="agent", seeds=(1,))

    # Fake agent: graded (up, down) per (pert, gene) — here, up for even gene index.
    def fake_agent(pert, gene, seed):
        return (0.9, 0.1) if int(gene[1:]) % 2 == 0 else (0.2, 0.8)

    rec = run_variant(
        df, variant, make_agent_row_predictor(fake_agent), seed=0, pert_frac=1.0, gene_frac=1.0
    )

    rows = df.to_dict("records")
    pairs = np.array([fake_agent(r["pert"], r["gene"], 1) for r in rows], dtype=float)
    exp = evaluate(df["label"].to_numpy(), pairs[:, 0], pairs[:, 1])
    assert rec.metrics["n_val"] == len(df)
    for k in ("auroc_de", "auroc_dir", "mean"):
        assert _eq(rec.metrics[k], exp[k])


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
