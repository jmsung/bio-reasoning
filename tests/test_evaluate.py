import numpy as np
import pandas as pd

from bio_reasoning.eval.track_a_score import (
    evaluate,
    evaluate_on_split,
    score_preds,
)


def test_evaluate_returns_metric_dict(de_labels):
    up = np.where(de_labels == "up", 1.0, 0.0)
    down = np.where(de_labels == "down", 1.0, 0.0)
    s = evaluate(de_labels, up, down)
    assert set(s) == {"auroc_de", "auroc_dir", "mean"}
    assert s["mean"] == 1.0


def test_evaluate_is_the_canonical_score_preds(de_labels):
    # score_preds is retained as a back-compat alias of evaluate.
    assert evaluate is score_preds


def _toy(n=2000, n_pert=120, n_gene=150, seed=1):
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "pert": [f"P{i}" for i in rng.integers(0, n_pert, n)],
            "gene": [f"G{i}" for i in rng.integers(0, n_gene, n)],
            "label": rng.choice(["up", "down", "none"], n),
        }
    )


def test_evaluate_on_split_scores_val_partition():
    df = _toy()
    rng = np.random.default_rng(0)
    up = rng.random(len(df))
    down = rng.random(len(df))
    r = evaluate_on_split(df, up, down, seed=0)
    assert set(r) == {"auroc_de", "auroc_dir", "mean", "n_val"}
    assert r["n_val"] > 0


def test_evaluate_on_split_is_deterministic():
    df = _toy()
    rng = np.random.default_rng(0)
    up, down = rng.random(len(df)), rng.random(len(df))
    a = evaluate_on_split(df, up, down, seed=0)
    b = evaluate_on_split(df, up, down, seed=0)
    assert a == b


def test_evaluate_on_split_matches_manual_slice():
    from bio_reasoning.eval.split import holdout_split

    df = _toy()
    rng = np.random.default_rng(0)
    up, down = rng.random(len(df)), rng.random(len(df))
    _, val = holdout_split(df, seed=0)
    manual = evaluate(df.label.to_numpy()[val], up[val], down[val])
    r = evaluate_on_split(df, up, down, seed=0)
    assert r["mean"] == manual["mean"] and r["n_val"] == len(val)
