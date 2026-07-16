"""End-to-end: drive scripts/track_a_prior_baseline.py main() offline.

Seeds a tiny train.csv and a full GO-category cache, points the script's module
paths at them, and asserts the whole read → annotate → predict → score → CV
pipeline runs without touching the network and prints the metric lines.
"""

import importlib.util
import re
from pathlib import Path

import pandas as pd

import bio_reasoning.features.gene_function as gf

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "track_a_prior_baseline.py"
_spec = importlib.util.spec_from_file_location("track_a_prior_baseline", _SCRIPT)
baseline = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(baseline)

# pert → seeded GO:BP terms → category (housekeeping / immune / other)
_GO_CACHE = {"Rpl3": ["translation"], "Il6": ["cytokine"], "Xyz": []}

_TRAIN_ROWS = [
    ("Rpl3", "g1", "up"),
    ("Rpl3", "g2", "up"),
    ("Rpl3", "g3", "none"),
    ("Rpl3", "g4", "up"),
    ("Il6", "g1", "down"),
    ("Il6", "g2", "down"),
    ("Il6", "g3", "none"),
    ("Il6", "g4", "none"),
    ("Xyz", "g1", "none"),
    ("Xyz", "g2", "up"),
    ("Xyz", "g3", "up"),
    ("Xyz", "g4", "down"),
]


def test_baseline_main_runs_offline_and_reports_metric(
    tmp_path, monkeypatch, capsys, write_go_cache
):
    train = tmp_path / "train.csv"
    pd.DataFrame(_TRAIN_ROWS, columns=["pert", "gene", "label"]).to_csv(train, index=False)
    cache = write_go_cache(_GO_CACHE, name="pert_go_category.json")

    monkeypatch.setattr(baseline, "TRAIN", train)
    monkeypatch.setattr(baseline, "CACHE", cache)

    # Full cache → the network fetch must never fire.
    def no_network(sym):
        raise AssertionError(f"network fetch attempted for {sym}")

    monkeypatch.setattr(gf, "_fetch_go_bp", no_network)

    baseline.main()

    out = capsys.readouterr().out
    assert f"train: {len(_TRAIN_ROWS)} rows" in out
    assert "prior (functional)" in out
    assert "constant (no signal)" in out
    # every printed baseline row carries a real de/dir/mean triple
    triples = re.findall(r"de=(\d\.\d{3})\s+dir=(nan|\d\.\d{3})\s+mean=(nan|\d\.\d{3})", out)
    assert len(triples) == 2  # constant + prior
