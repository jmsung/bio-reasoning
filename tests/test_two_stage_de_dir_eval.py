"""Goal 3 test: scripts/two_stage_de_dir_eval.py runs offline and prints a table.

Drives main() on seeded synthetic data with pre-seeded GO caches (pert + target
gene), patching the data paths so no network is touched. Asserts the honest
comparison table (no-signal / prior / char-ngram / GO-term, holdout + CV) plus a
verdict line are emitted.
"""

import importlib.util
from pathlib import Path

import pandas as pd

import bio_reasoning.features.gene_function as gf

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "two_stage_de_dir_eval.py"
_spec = importlib.util.spec_from_file_location("two_stage_de_dir_eval", _SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def _signal_df() -> pd.DataFrame:
    rows = []
    for i in range(300):
        tag, label = {0: ("up", "up"), 1: ("dn", "down"), 2: ("xx", "none")}[i % 3]
        rows.append((f"P{i}", f"G{tag}{i}", label))
    return pd.DataFrame(rows, columns=["pert", "gene", "label"])


def test_main_runs_offline_and_prints_table(tmp_path, monkeypatch, capsys, write_go_cache):
    df = _signal_df()
    train = tmp_path / "train.csv"
    df.to_csv(train, index=False)
    # GO caches carry a per-kind term so both vocabularies are non-empty offline.
    pert_go = {p: [f"pgo_{i % 3}"] for i, p in enumerate(df.pert)}
    gene_go = {g: [f"ggo_{g[1:3]}"] for g in df.gene}  # tag = 'up'/'dn'/'xx'
    pc = write_go_cache(pert_go, name="pert_go_category.json")
    gcache = write_go_cache(gene_go, name="gene_go_bp.json")

    monkeypatch.setattr(mod, "TRAIN", train)
    monkeypatch.setattr(mod, "PERT_CACHE", pc)
    monkeypatch.setattr(mod, "GENE_CACHE", gcache)
    monkeypatch.setattr(gf, "_fetch_go_bp", lambda sym: (_ for _ in ()).throw(AssertionError(sym)))

    mod.main()

    out = capsys.readouterr().out
    assert "dual-OOD holdout val" in out
    assert "two-stage char-ngram" in out
    assert "two-stage GO-term" in out
    assert "5-fold doubly-disjoint CV" in out
    assert "Verdict:" in out
