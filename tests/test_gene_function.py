import json

import bio_reasoning.features.gene_function as gf
from bio_reasoning.features.gene_function import annotate_perts, classify


def test_classify_housekeeping_keyword_hit():
    assert classify("Rpl3", ["cytoplasmic translation", "ribosome biogenesis"]) == "housekeeping"


def test_classify_immune_keyword_hit():
    assert classify("Il6", ["cytokine production", "inflammatory response"]) == "immune"


def test_classify_tie_and_empty_return_other():
    assert classify("X", ["translation", "cytokine"]) == "other"  # 1 vs 1 tie
    assert classify("X", []) == "other"
    assert classify("X", ["unrelated term"]) == "other"


def test_annotate_cache_hit_is_offline(tmp_path, monkeypatch):
    cache = tmp_path / "go.json"
    cache.write_text(json.dumps({"Rpl3": ["translation"], "Il6": ["cytokine"]}))

    def boom(sym):  # must not be called on a full cache hit
        raise AssertionError(f"_fetch_go_bp called for {sym}")

    monkeypatch.setattr(gf, "_fetch_go_bp", boom)
    out = annotate_perts(["Rpl3", "Il6"], cache)
    assert out == {"Rpl3": "housekeeping", "Il6": "immune"}


def test_annotate_miss_fetches_dedups_and_writes(tmp_path, monkeypatch):
    cache = tmp_path / "sub" / "go.json"  # parent does not exist yet
    calls = []

    def fake_fetch(sym):
        calls.append(sym)
        return {"Rpl3": ["ribosome"], "Il6": ["interferon"]}[sym]

    monkeypatch.setattr(gf, "_fetch_go_bp", fake_fetch)
    out = annotate_perts(["Rpl3", "Il6", "Rpl3"], cache)  # duplicate Rpl3

    assert calls == ["Rpl3", "Il6"]  # dedup: each fetched once
    assert out == {"Rpl3": "housekeeping", "Il6": "immune"}
    assert cache.exists()
    assert json.loads(cache.read_text()) == {"Rpl3": ["ribosome"], "Il6": ["interferon"]}


def test_annotate_fetch_failure_defaults_to_other(tmp_path, monkeypatch):
    cache = tmp_path / "go.json"

    def raiser(sym):
        raise RuntimeError("network down")

    monkeypatch.setattr(gf, "_fetch_go_bp", raiser)
    out = annotate_perts(["Whatever"], cache)
    assert out == {"Whatever": "other"}
    assert json.loads(cache.read_text()) == {"Whatever": []}
