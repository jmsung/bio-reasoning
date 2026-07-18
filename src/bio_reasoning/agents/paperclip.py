"""paperclip — an agentic literature-search demo over perturbation biology.

Given a perturbation-biology question (e.g. *"Does knockdown of Spi1/PU.1 change
Csf1r expression in macrophages, and in which direction?"*) this agent:

  1. **searches** an open, no-auth literature API — Europe PMC REST
     (https://www.ebi.ac.uk/europepmc/webservices/rest/search, free, no key),
  2. **reads** the top abstracts, and
  3. **reasons** over them with an LLM (gpt-oss-120b via OpenRouter, reusing the
     repo's :func:`~bio_reasoning.agents.retrieval_agent.openrouter_llm_fn`) to
     emit a STRUCTURED, CITED answer: does the target respond (is it
     differentially expressed)? in which direction (up / down)? a confidence, and
     the exact PMIDs it used, plus a short reasoning trace.

Both external dependencies are injected seams — ``fetch`` (HTTP) and ``llm_fn`` —
so the agent is fully offline-testable (see ``tests/test_paperclip.py``).

Scope / honesty
---------------
This is a **portfolio / showcase piece**, not a competition submission. On the
BioReasoning challenge's differential-expression axis, external-knowledge
retrieval lands at *parity*, not above — see
``knowledge/wiki/findings/external-knowledge-does-not-crack-de.md``. Worse,
arbitrary literature is off the challenge's allowed-data list (PerturbQA +
Tahoe-100M only), so paperclip must NOT be used for a Kaggle submission. Its
value is a clean demonstration of agentic tool-use + honest, cited scientific
reasoning.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field

# Reuse the repo's LLM seam + default OpenRouter client — do not reinvent.
from bio_reasoning.agents.retrieval_agent import LlmFn, openrouter_llm_fn

__all__ = [
    "Paper",
    "PaperclipResult",
    "LlmFn",
    "answer_question",
    "build_prompt",
    "europepmc_search",
    "make_search_fn",
    "openrouter_llm_fn",
    "parse_answer",
]

EUROPEPMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

# fetch(url) -> raw response body. Injectable so HTTP is mocked in tests.
FetchFn = Callable[[str], str]
# search_fn(query, limit) -> papers. Injectable so the search step is mocked.
SearchFn = Callable[[str, int], "list[Paper]"]


# ---------------------------------------------------------------------------
# Retrieval — Europe PMC REST (open, no auth)
# ---------------------------------------------------------------------------


@dataclass
class Paper:
    """One retrieved paper: enough to cite and to feed the LLM its abstract."""

    pmid: str
    title: str
    abstract: str
    year: str
    authors: str
    url: str


def _http_get(url: str, *, timeout_s: int = 20) -> str:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    req.add_header("Connection", "close")
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return resp.read().decode()


def europepmc_search(
    query: str, *, limit: int = 8, sort: str | None = None, fetch: FetchFn = _http_get
) -> list[Paper]:
    """Search Europe PMC and return up to ``limit`` papers that have an abstract.

    Uses ``resultType=core`` so each hit carries ``abstractText``. Abstract-less
    hits are dropped (no text to reason over). Default sort is Europe PMC's
    relevance ranking (``sort`` omitted); pass e.g. ``"CITED desc"`` or
    ``"P_PDATE_D desc"`` to override. Any network/parse failure degrades to an
    empty list — the caller reports "no evidence found", never crashes.
    """
    params = {
        "query": query,
        "format": "json",
        "resultType": "core",
        "pageSize": str(limit),
    }
    if sort:
        params["sort"] = sort
    url = EUROPEPMC_SEARCH + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    try:
        data = json.loads(fetch(url))
    except Exception:
        return []

    results = ((data.get("resultList") or {}).get("result")) or []
    papers: list[Paper] = []
    for r in results:
        abstract = (r.get("abstractText") or "").strip()
        if not abstract:
            continue
        pmid = str(r.get("pmid") or r.get("id") or "")
        papers.append(
            Paper(
                pmid=pmid,
                title=(r.get("title") or "").strip(),
                abstract=abstract,
                year=str(r.get("pubYear") or ""),
                authors=(r.get("authorString") or "").strip(),
                url=f"https://europepmc.org/abstract/MED/{pmid}" if pmid else "",
            )
        )
        if len(papers) >= limit:
            break
    return papers


def make_search_fn(*, fetch: FetchFn = _http_get) -> SearchFn:
    """Build a :data:`SearchFn` ``(query, limit) -> [Paper]`` backed by Europe PMC."""

    def _fn(query: str, limit: int) -> list[Paper]:
        return europepmc_search(query, limit=limit, fetch=fetch)

    return _fn


# ---------------------------------------------------------------------------
# Prompt + parse
# ---------------------------------------------------------------------------

_INSTRUCTIONS = """\
You are an expert molecular biologist answering a perturbation-biology question
strictly from the paper abstracts provided below. Do not use outside knowledge;
if the abstracts are insufficient, say so via a low confidence.

QUESTION
--------
{question}

RETRIEVED ABSTRACTS
-------------------
{papers}
-------------------

Reason step by step:
  1. Which abstracts, if any, bear on whether the target gene's expression
     responds to the perturbation? Cite them by PMID. Indirect or mechanistic
     evidence counts (e.g. "the perturbed gene activates the target's promoter",
     or "pathway X is suppressed") — weigh it, don't discard it.
  2. Does the target RESPOND (is it differentially expressed)?
  3. If it responds, is the change UP or DOWN? If the abstracts disagree or are
     silent on direction, use "unclear".
  4. Set confidence to match evidence strength: high for direct measured effects,
     MODERATE (~0.4-0.7) for consistent indirect/mechanistic evidence, low only
     when the abstracts truly do not speak to the question. Never fabricate an
     effect the abstracts do not support, but do commit when they point one way.

After your reasoning, output EXACTLY ONE final line of JSON and nothing after it:
{{"responds": <true|false>, "direction": "<up|down|unclear>", \
"confidence": <0.0-1.0>, "citations": [<PMIDs you actually used>]}}
"""


def build_prompt(question: str, papers: list[Paper]) -> str:
    """Render the question + numbered abstracts (with PMIDs) into the LLM prompt."""
    blocks = []
    for i, p in enumerate(papers, 1):
        head = f"[{i}] PMID {p.pmid} ({p.year}) — {p.title}"
        blocks.append(f"{head}\n{p.abstract}")
    return _INSTRUCTIONS.format(question=question, papers="\n\n".join(blocks))


_JSON_RE = re.compile(r"\{[^{}]*\"direction\"[^{}]*\}")


def parse_answer(text: str) -> dict | None:
    """Extract the last structured-answer JSON object from the model text.

    Returns a normalized dict ``{responds, direction, confidence, citations}``
    (direction lower-cased, confidence clamped to [0, 1], citations as strings),
    or ``None`` if no parseable object is present.
    """
    for blob in reversed(_JSON_RE.findall(text or "")):
        try:
            d = json.loads(blob)
            responds = bool(d["responds"])
            direction = str(d["direction"]).strip().lower()
            confidence = float(d["confidence"])
            citations = [str(c) for c in (d.get("citations") or [])]
        except (ValueError, KeyError, TypeError):
            continue
        if direction not in {"up", "down", "unclear"}:
            direction = "unclear"
        return {
            "responds": responds,
            "direction": direction,
            "confidence": min(max(confidence, 0.0), 1.0),
            "citations": citations,
        }
    return None


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


@dataclass
class PaperclipResult:
    """The agent's cited answer for one question, with its tool trace."""

    question: str
    papers: list[Paper]
    responds: bool | None
    direction: str | None
    confidence: float | None
    citations: list[str]
    reasoning: str
    parsed: bool
    tokens: dict[str, float]
    trace: list[dict] = field(default_factory=list)


def answer_question(
    question: str,
    *,
    search_fn: SearchFn,
    llm_fn: LlmFn,
    top_k: int = 8,
    seed: int = 42,
) -> PaperclipResult:
    """Search literature, read abstracts, and emit a structured cited answer.

    Returns a :class:`PaperclipResult`. Degrades gracefully: no search hits →
    an unparsed result with an empty paper list (the LLM is not called); an LLM
    error or unparseable output → ``parsed=False`` with the raw reasoning kept.
    """
    trace: list[dict] = []
    papers = search_fn(question, top_k)
    trace.append(
        {
            "tool": "europepmc_search",
            "query": question,
            "n_hits": len(papers),
            "pmids": [p.pmid for p in papers],
        }
    )
    if not papers:
        return PaperclipResult(question, [], None, None, None, [], "", False, {}, trace)

    prompt = build_prompt(question, papers)
    try:
        text, tokens = llm_fn(prompt, seed)
    except Exception as e:
        trace.append({"tool": "llm", "error": str(e)})
        return PaperclipResult(question, papers, None, None, None, [], "", False, {}, trace)

    ans = parse_answer(text)
    trace.append({"tool": "llm", "parsed": ans is not None})
    if ans is None:
        return PaperclipResult(question, papers, None, None, None, [], text, False, tokens, trace)
    return PaperclipResult(
        question=question,
        papers=papers,
        responds=ans["responds"],
        direction=ans["direction"],
        confidence=ans["confidence"],
        citations=ans["citations"],
        reasoning=text,
        parsed=True,
        tokens=tokens,
        trace=trace,
    )
