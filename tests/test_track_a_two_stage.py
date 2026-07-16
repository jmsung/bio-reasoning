"""Goal 2 tests for the two-stage DE×DIR model.

The model factors the Track A label into P(DE) (differentially expressed vs
none) and P(up | DE) (direction), then recombines ``up = DE·DIR`` and
``down = DE·(1−DIR)`` — exactly the decomposition the metric scores. Tests pin
the recombination identity and that both heads learn a string-carried signal
that survives an OOD (unseen-gene) split.
"""

import numpy as np
import pandas as pd

from bio_reasoning.eval.track_a_score import evaluate
from bio_reasoning.models.track_a_two_stage import TwoStageDEDIR


def _signal_df(n_genes: int, seed: int) -> pd.DataFrame:
    """Synthetic data where the gene *string* carries DE and direction.

    Genes whose name contains ``up`` are up-regulated, ``dn`` down-regulated,
    others none. Char-ngram features can recover this on genes never seen at
    fit time — the OOD premise.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n_genes):
        kind = i % 3
        tag, label = {0: ("up", "up"), 1: ("dn", "down"), 2: ("xx", "none")}[kind]
        gene = f"G{tag}s{seed}n{i}"  # seed in the id → disjoint gene sets across seeds
        pert = f"P{rng.integers(0, 1000)}"
        rows.append((pert, gene, label))
    return pd.DataFrame(rows, columns=["pert", "gene", "label"])


def test_recombination_identity_holds():
    tr = _signal_df(120, seed=0)
    m = TwoStageDEDIR().fit(tr.pert, tr.gene, tr.label.to_numpy())
    up, down = m.predict(tr.pert, tr.gene)
    p_de = up + down
    assert np.all(up >= 0) and np.all(down >= 0)
    assert np.all(p_de <= 1.0 + 1e-9)
    # DIR score = up / (up+down) is a valid probability wherever DE > 0.
    nz = p_de > 1e-9
    dir_score = up[nz] / p_de[nz]
    assert np.all((dir_score >= -1e-9) & (dir_score <= 1 + 1e-9))


def test_learns_string_signal_on_unseen_genes():
    train = _signal_df(180, seed=1)
    test = _signal_df(90, seed=99)  # disjoint gene ids, same string pattern
    assert not (set(train.gene) & set(test.gene))
    m = TwoStageDEDIR().fit(train.pert, train.gene, train.label.to_numpy())
    up, down = m.predict(test.pert, test.gene)
    r = evaluate(test.label.to_numpy(), up, down)
    assert r["auroc_de"] > 0.75
    assert r["auroc_dir"] > 0.75


def test_predict_returns_aligned_arrays():
    tr = _signal_df(60, seed=2)
    m = TwoStageDEDIR().fit(tr.pert, tr.gene, tr.label.to_numpy())
    up, down = m.predict(["Pnew"], ["Gnew"])
    assert up.shape == down.shape == (1,)
