"""Offline unit tests for the paperclip literature-search agent.

Both external dependencies — the Europe PMC HTTP API and the LLM — are injected,
so the whole suite is deterministic and never touches the network.
"""

from __future__ import annotations

import json

import pytest

from bio_reasoning.agents.paperclip import (
    Paper,
    PaperclipResult,
    answer_question,
    build_prompt,
    europepmc_search,
    parse_answer,
)

# A canned Europe PMC `resultType=core` search response (two hits, one with no
# abstract — the agent must drop abstract-less papers).
_EPMC_JSON = json.dumps(
    {
        "hitCount": 2,
        "resultList": {
            "result": [
                {
                    "id": "11111111",
                    "source": "MED",
                    "pmid": "11111111",
                    "doi": "10.1/abc",
                    "title": "PU.1 (Spi1) drives Csf1r expression in macrophages.",
                    "authorString": "Smith J, Doe A.",
                    "pubYear": "2019",
                    "abstractText": "Knockdown of Spi1 reduced Csf1r transcription in BMDMs.",
                },
                {
                    "id": "22222222",
                    "source": "MED",
                    "pmid": "22222222",
                    "title": "A paper with no abstract field.",
                    "authorString": "Roe B.",
                    "pubYear": "2020",
                },
            ]
        },
    }
)


def _fake_fetch(_url: str) -> str:
    return _EPMC_JSON


def test_europepmc_search_parses_and_drops_abstractless():
    papers = europepmc_search("Spi1 Csf1r", limit=5, fetch=_fake_fetch)
    assert len(papers) == 1  # the abstract-less hit is dropped
    p = papers[0]
    assert p.pmid == "11111111"
    assert "Csf1r" in p.title
    assert p.year == "2019"
    assert "reduced Csf1r" in p.abstract
    assert p.url.endswith("11111111")


def test_europepmc_search_url_is_encoded_and_no_auth():
    seen = {}

    def capture(url: str) -> str:
        seen["url"] = url
        return _EPMC_JSON

    europepmc_search("Spi1 AND Csf1r", limit=3, fetch=capture)
    url = seen["url"]
    assert url.startswith("https://www.ebi.ac.uk/europepmc/webservices/rest/search")
    assert "format=json" in url and "pageSize=3" in url
    assert "sort=" not in url  # default relevance ranking — no sort override
    assert "Spi1%20AND%20Csf1r" in url or "Spi1+AND+Csf1r" in url


def test_build_prompt_lists_papers_with_pmids():
    papers = [
        Paper("11111111", "PU.1 drives Csf1r.", "Down-regulated.", "2019", "Smith J", "url1"),
    ]
    prompt = build_prompt("Does Spi1 knockdown change Csf1r?", papers)
    assert "Spi1 knockdown" in prompt
    assert "PMID 11111111" in prompt
    assert "Down-regulated." in prompt


def test_parse_answer_last_object_wins_and_normalizes():
    text = (
        'draft {"responds": false, "direction": "unclear", "confidence": 0.2, "citations": []}\n'
        'final {"responds": true, "direction": "DOWN", "confidence": 1.5, '
        '"citations": ["11111111", 22222222]}'
    )
    ans = parse_answer(text)
    assert ans is not None
    assert ans["responds"] is True
    assert ans["direction"] == "down"  # lower-cased
    assert ans["confidence"] == 1.0  # clamped to [0, 1]
    assert ans["citations"] == ["11111111", "22222222"]  # coerced to str


def test_parse_answer_none_on_garbage():
    assert parse_answer("no json here") is None
    assert parse_answer('{"foo": 1}') is None


def test_answer_question_end_to_end_offline():
    def fake_search(query: str, limit: int) -> list[Paper]:
        return [
            Paper("11111111", "PU.1 drives Csf1r.", "Knockdown reduced Csf1r.", "2019", "S", "u1"),
        ]

    def fake_llm(prompt: str, seed: int) -> tuple[str, dict[str, float]]:
        assert "Csf1r" in prompt  # the prompt carries the retrieved abstract
        return (
            "The abstract shows knockdown lowers Csf1r.\n"
            '{"responds": true, "direction": "down", "confidence": 0.8, '
            '"citations": ["11111111"]}',
            {"total_tokens": 123},
        )

    res = answer_question(
        "Does Spi1 knockdown change Csf1r in macrophages?",
        search_fn=fake_search,
        llm_fn=fake_llm,
        top_k=5,
    )
    assert isinstance(res, PaperclipResult)
    assert res.parsed is True
    assert res.responds is True
    assert res.direction == "down"
    assert res.confidence == pytest.approx(0.8)
    assert res.citations == ["11111111"]
    assert len(res.papers) == 1
    assert res.tokens["total_tokens"] == 123
    tools = [t["tool"] for t in res.trace]
    assert tools == ["europepmc_search", "llm"]


def test_answer_question_no_papers_short_circuits():
    def empty_search(query: str, limit: int) -> list[Paper]:
        return []

    def llm_should_not_run(prompt: str, seed: int):
        raise AssertionError("LLM must not be called when no papers were found")

    res = answer_question(
        "an obscure question with no hits",
        search_fn=empty_search,
        llm_fn=llm_should_not_run,
    )
    assert res.papers == []
    assert res.parsed is False
    assert res.responds is None
    assert res.trace[-1]["tool"] == "europepmc_search"


def test_answer_question_parse_failure_degrades_gracefully():
    def fake_search(query: str, limit: int) -> list[Paper]:
        return [Paper("1", "t", "a", "2020", "x", "u")]

    def bad_llm(prompt: str, seed: int) -> tuple[str, dict[str, float]]:
        return "I could not determine an answer.", {"total_tokens": 7}

    res = answer_question("q", search_fn=fake_search, llm_fn=bad_llm)
    assert res.parsed is False
    assert res.responds is None
    assert res.reasoning == "I could not determine an answer."
