import numpy as np
import pandas as pd

from bio_reasoning.eval.split import assert_leak_free, doubly_disjoint_folds


def _toy(n=600, n_pert=30, n_gene=40, seed=1):
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "pert": [f"P{i}" for i in rng.integers(0, n_pert, n)],
            "gene": [f"G{i}" for i in rng.integers(0, n_gene, n)],
            "label": rng.choice(["up", "down", "none"], n),
        }
    )


def test_folds_are_leak_free():
    df = _toy()
    folds = doubly_disjoint_folds(df, k=5, seed=0)
    assert len(folds) == 5
    for tr, ev in folds:
        assert len(ev) > 0
        # no shared pert or gene between train and eval
        assert_leak_free(df, tr, ev)


def test_eval_sets_are_disjoint_across_folds():
    df = _toy()
    seen: set[int] = set()
    for _, ev in doubly_disjoint_folds(df, k=5, seed=0):
        s = set(ev.tolist())
        assert not (s & seen)  # a row lands in at most one eval fold
        seen |= s


def test_split_is_deterministic():
    df = _toy()
    a = doubly_disjoint_folds(df, k=5, seed=0)
    b = doubly_disjoint_folds(df, k=5, seed=0)
    for (t1, e1), (t2, e2) in zip(a, b, strict=False):
        assert np.array_equal(t1, t2) and np.array_equal(e1, e2)
