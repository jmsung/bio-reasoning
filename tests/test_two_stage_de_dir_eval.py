"""Goal 3 test: scripts/two_stage_de_dir_eval.py runs offline and prints a table.

Drives main() on seeded synthetic data with a gene-string signal, patching the
data path and the GO cache so no network is touched. Asserts the honest
comparison table (no-signal / prior / two-stage, holdout + CV) is emitted.
"""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

import bio_reasoning.features.gene_function as gf

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "two_stage_de_dir_eval.py"
_spec = importlib.util.spec_from_file_location("two_stage_de_dir_eval", _SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def _signal_df(seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(300):
        tag, label = {0: ("up", "up"), 1: ("dn", "down"), 2: ("xx", "none")}[i % 3]
        rows.append((f"P{rng.integers(0, 400)}", f"G{tag}{i}", label))
    return pd.DataFrame(rows, columns=["pert", "gene", "label"])


def test_main_runs_offline_and_prints_table(tmp_path, monkeypatch, capsys, write_go_cache):
    df = _signal_df()
    train = tmp_path / "train.csv"
    df.to_csv(train, index=False)
    cache = write_go_cache({p: [] for p in df.pert.unique()}, name="pert_go_category.json")

    monkeypatch.setattr(mod, "TRAIN", train)
    monkeypatch.setattr(mod, "CACHE", cache)
    monkeypatch.setattr(gf, "_fetch_go_bp", lambda sym: (_ for _ in ()).throw(AssertionError(sym)))

    mod.main()

    out = capsys.readouterr().out
    assert "dual-OOD holdout val" in out
    assert "two-stage (learned)" in out
    assert "5-fold doubly-disjoint CV" in out
    assert "Verdict:" in out
