"""Offline tests for the LLM-as-optimizer proposer (injected propose_fn, no network)."""

from __future__ import annotations

from bio_reasoning.trial_loop.llm_proposer import make_llm_proposer
from bio_reasoning.trial_loop.types import Variant


def _fallback():
    return lambda reflection, history: Variant(id="fallback-bandit")


def test_valid_json_proposal_becomes_a_variant():
    fn = lambda r: '{"n_few_shot": 4, "retrieval": "go_category", "n_samples": 5}'  # noqa: E731
    p = make_llm_proposer(fn, fallback=_fallback())
    v = p("reflection", [])
    assert v.id == "llm-nfs4-go_category-s5"
    assert v.n_few_shot == 4 and v.retrieval == "go_category" and len(v.seeds) == 5


def test_json_embedded_in_reasoning_text_is_extracted():
    def fn(r):
        return 'nfs4 looks best so far.\nAnswer: {"n_few_shot": 4, "retrieval": "random", "n_samples": 3} done.'

    p = make_llm_proposer(fn, fallback=_fallback())
    assert p("", []).id == "llm-nfs4-random-s3"


def test_malformed_output_falls_back_to_bandit():
    fn = lambda r: "I think we should use more few-shot examples."  # no JSON  # noqa: E731
    p = make_llm_proposer(fn, fallback=_fallback())
    assert p("", []).id == "fallback-bandit"


def test_invalid_retrieval_falls_back():
    fn = lambda r: '{"n_few_shot": 2, "retrieval": "telepathy", "n_samples": 3}'  # noqa: E731
    p = make_llm_proposer(fn, fallback=_fallback())
    assert p("", []).id == "fallback-bandit"


def test_ruled_out_approach_falls_back():
    # LLM proposes a dead static channel via the approach tag → guard rejects, bandit takes over
    def fn(r):
        return (
            '{"n_few_shot": 2, "retrieval": "random", "n_samples": 3, "approach": "string-degree"}'
        )

    p = make_llm_proposer(fn, fallback=_fallback())
    assert p("", []).id == "fallback-bandit"


def test_bad_sample_count_falls_back():
    fn = lambda r: '{"n_few_shot": 2, "retrieval": "random", "n_samples": 99}'  # noqa: E731
    p = make_llm_proposer(fn, fallback=_fallback())
    assert p("", []).id == "fallback-bandit"
