"""Goal 4 tests for scripts/ood_val_baselines.py.

Two layers: (1) the leak-free / inflation *invariants* of the demo helpers on
seeded data — a per-pert memorizing baseline collapses to chance under the
dual-OOD split but scores above chance under naive random-row CV; (2) an offline
end-to-end drive of main() that prints the honest table without touching the
network.
"""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

import bio_reasoning.features.gene_function as gf
from bio_reasoning.eval.split import doubly_disjoint_folds

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ood_val_baselines.py"
_spec = importlib.util.spec_from_file_location("ood_val_baselines", _SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def _signal_df(seed: int = 0) -> pd.DataFrame:
    """Synthetic Track A data with a real *per-pert* direction/DE signal.

    up-perts are mostly `up`, down-perts mostly `down`, quiet-perts mostly
    `none`. A predictor that memorizes pert identity therefore beats chance —
    but only when it has seen the pert in training.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for p in range(60):
        kind = p % 3  # 0=up, 1=down, 2=quiet
        probs = {0: [0.7, 0.0, 0.3], 1: [0.0, 0.7, 0.3], 2: [0.05, 0.05, 0.9]}[kind]
        for _ in range(40):
            label = rng.choice(["up", "down", "none"], p=probs)
            rows.append((f"P{p}", f"G{rng.integers(0, 80)}", label))
    return pd.DataFrame(rows, columns=["pert", "gene", "label"])


def test_memorizing_baseline_collapses_under_dual_ood():
    df = _signal_df()
    ood = doubly_disjoint_folds(df, k=5, seed=0)
    naive = mod._random_folds(len(df), 5, 0)
    mem_ood = mod._memorizing_cv_mean(df, ood)
    mem_naive = mod._memorizing_cv_mean(df, naive)
    # Unseen perts → 0.5/0.5 fallback → exactly chance on the OOD split.
    assert abs(mem_ood - 0.5) < 1e-6
    # Seen perts under naive CV → real above-chance signal (the inflation).
    assert mem_naive > 0.55
    assert mem_naive > mem_ood


def test_fixed_prediction_cv_mean_is_split_stable():
    # A *fixed* (not fold-fitted) predictor can't leak: its score doesn't depend
    # on which rows are held out beyond sampling noise.
    df = _signal_df()
    rng = np.random.default_rng(1)
    up, down = rng.random(len(df)), rng.random(len(df))
    ood = mod._cv_mean(df, doubly_disjoint_folds(df, k=5, seed=0), up, down)
    naive = mod._cv_mean(df, mod._random_folds(len(df), 5, 0), up, down)
    assert abs(naive - ood) < 0.05


def test_main_runs_offline_and_prints_honest_table(tmp_path, monkeypatch, capsys, write_go_cache):
    df = _signal_df()
    train = tmp_path / "train.csv"
    df.to_csv(train, index=False)
    # Full GO cache (every pert → "other") so annotate never hits the network.
    cache = write_go_cache({p: [] for p in df.pert.unique()}, name="pert_go_category.json")

    monkeypatch.setattr(mod, "TRAIN", train)
    monkeypatch.setattr(mod, "CACHE", cache)

    def no_network(sym):
        raise AssertionError(f"network fetch attempted for {sym}")

    monkeypatch.setattr(gf, "_fetch_go_bp", no_network)

    mod.main()

    out = capsys.readouterr().out
    assert "honest baseline table on the dual-OOD held-out val split" in out
    assert "no-signal (0.5/0.5)" in out and "0.500" in out
    assert "why a naive CV inflates" in out
    assert "memorizing (per-pert)" in out
    assert "Track B (reported): CV 0.675" in out
