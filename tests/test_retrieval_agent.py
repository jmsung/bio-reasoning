"""Offline unit tests for the Track B retrieval-augmented per-row predictor."""

from __future__ import annotations

import json

import pytest

from bio_reasoning.agents.retrieval_agent import (
    RowResult,
    make_agent_fn,
    parse_prediction,
    predict_row,
    retrieve,
    to_up_down,
)


@pytest.fixture()
def caches(tmp_path):
    """Pre-populated GO caches so retrieval never hits the network."""
    pert_cache = tmp_path / "pert.json"
    gene_cache = tmp_path / "gene.json"
    pert_cache.write_text(json.dumps({"Rpl13": ["translation", "ribosome biogenesis"]}))
    gene_cache.write_text(json.dumps({"Actb": ["cytoskeleton organization"]}))
    return pert_cache, gene_cache


def test_parse_prediction_last_object_wins():
    text = 'draft {"de_prob": 0.1, "dir_prob": 0.9}\nfinal {"de_prob": 0.7, "dir_prob": 0.2}'
    assert parse_prediction(text) == (0.7, 0.2)


def test_parse_prediction_clamps_out_of_range():
    assert parse_prediction('{"de_prob": 1.4, "dir_prob": -0.3}') == (1.0, 0.0)


def test_parse_prediction_none_on_garbage():
    assert parse_prediction("no json here") is None
    assert parse_prediction('{"foo": 1}') is None


def test_to_up_down_sum_is_de_prob():
    up, down = to_up_down(0.6, 0.75)
    assert up == pytest.approx(0.45)
    assert down == pytest.approx(0.15)
    assert up + down == pytest.approx(0.6)


def test_retrieve_builds_context_and_trace(caches):
    pert_cache, gene_cache = caches
    r = retrieve("Rpl13", "Actb", pert_cache=pert_cache, gene_cache=gene_cache)
    assert "Rpl13" in r.context and "Actb" in r.context
    assert r.category == "housekeeping"  # 'ribosome'/'translation' keywords
    assert 0.0 < r.prior_up < 1.0
    tools = [c["tool"] for c in r.trace]
    assert tools == ["get_pert_go_category", "get_gene_go"]  # no string_fn -> 2 tools


def test_retrieve_string_edge_flag(caches):
    pert_cache, gene_cache = caches
    r = retrieve(
        "Rpl13",
        "Actb",
        pert_cache=pert_cache,
        gene_cache=gene_cache,
        string_fn=lambda g: [("Actb", 0.9), ("Gapdh", 0.5)],
    )
    assert r.direct_edge is True
    assert "DIRECT Rpl13->Actb" in r.context


def test_predict_row_parses_calibrated_output(caches):
    pert_cache, gene_cache = caches

    def llm(prompt, seed):
        return 'reasoning...\n{"de_prob": 0.8, "dir_prob": 0.25}', {"total_tokens": 42}

    res = predict_row("Rpl13", "Actb", 42, llm_fn=llm, pert_cache=pert_cache, gene_cache=gene_cache)
    assert isinstance(res, RowResult)
    assert res.parsed is True
    assert res.up == pytest.approx(0.2)
    assert res.down == pytest.approx(0.6)
    assert res.abstained is False
    assert res.tokens["total_tokens"] == 42


def test_predict_row_parse_fail_returns_zero_zero(caches):
    pert_cache, gene_cache = caches

    def llm(prompt, seed):
        return "model said nothing useful", {"total_tokens": 5}

    res = predict_row("Rpl13", "Actb", 42, llm_fn=llm, pert_cache=pert_cache, gene_cache=gene_cache)
    assert (res.up, res.down) == (0.0, 0.0)
    assert res.parsed is False
    assert res.abstained is True  # a (0,0) row must be floored downstream


def test_predict_row_llm_exception_degrades_one_row(caches):
    pert_cache, gene_cache = caches

    def boom(prompt, seed):
        raise RuntimeError("rate limit")

    res = predict_row(
        "Rpl13", "Actb", 42, llm_fn=boom, pert_cache=pert_cache, gene_cache=gene_cache
    )
    assert (res.up, res.down) == (0.0, 0.0)
    assert res.parsed is False


def test_make_agent_fn_matches_loop_seam(caches):
    pert_cache, gene_cache = caches

    def llm(prompt, seed):
        return '{"de_prob": 0.5, "dir_prob": 0.6}', {}

    fn = make_agent_fn(llm, pert_cache=pert_cache, gene_cache=gene_cache)
    up, down = fn("Rpl13", "Actb", 42)
    assert up == pytest.approx(0.3)
    assert down == pytest.approx(0.2)
