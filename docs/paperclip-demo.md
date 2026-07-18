# paperclip — agentic literature-search demo

**A demonstration of agentic literature synthesis over perturbation biology.**
Ask a perturbation question in plain English; paperclip searches the open
literature, reads the abstracts, and an LLM reasons over them to emit a
**structured, cited** answer — does the target gene respond, in which direction,
with what confidence, and *citing the exact PMIDs it used*.

> **Scope — portfolio piece, not a competition entry.** On the BioReasoning
> challenge's differential-expression (DE) axis, external-knowledge retrieval
> lands at **parity, not above** — the DE wall is format-independent (see
> [`knowledge/wiki/findings/external-knowledge-does-not-crack-de.md`](../knowledge/wiki/findings/external-knowledge-does-not-crack-de.md)).
> Worse, arbitrary literature is **off the challenge's allowed-data list**
> (PerturbQA + Tahoe-100M only), so paperclip **must not** be used for a Kaggle
> submission. Its value is showing clean agentic tool-use and honest, calibrated
> scientific reasoning — not a leaderboard number.

## What it does

```
question ─▶ Europe PMC REST search ─▶ top-k abstracts ─▶ LLM reasons ─▶ {responds, direction, confidence, citations}
             (open, no API key)          (real papers)     (gpt-oss-120b)      + short reasoning trace
```

1. **Search** — [Europe PMC REST](https://europepmc.org/RestfulWebService)
   (`/search`, free, no key), `resultType=core` so each hit carries its
   abstract. Abstract-less hits are dropped; relevance-ranked by default.
2. **Read** — the top-k abstracts are assembled into a prompt, each tagged with
   its PMID so the model can cite precisely.
3. **Reason** — an LLM (gpt-oss-120b via OpenRouter, reusing the repo's existing
   `openrouter_llm_fn` client) reasons step-by-step and emits one line of JSON:
   `{"responds", "direction", "confidence", "citations"}`. Mechanistic/indirect
   evidence is weighed with *graded* confidence; the model is told never to
   fabricate an effect the abstracts don't support.

Both external seams — the HTTP call and the LLM — are **injected**, so the whole
unit-test suite is offline and deterministic (`tests/test_paperclip.py`).

## Run it

```bash
# default question (Spi1/PU.1 → Csf1r)
uv run python scripts/paperclip_demo.py

# your own question; --json for the full structured result + tool trace
uv run python scripts/paperclip_demo.py --top-k 6 "Spi1 PU.1 knockout Csf1r expression macrophage"
uv run python scripts/paperclip_demo.py --json "MafB transcriptional regulation macrophage identity Csf1r"
```

Requires `OPENROUTER_API_KEY` in `.env.local` (key contents are never printed).
Retrieval works best with **entity-focused** queries (gene symbols + tissue +
"knockout/knockdown") rather than long English sentences — Europe PMC free-text
relevance is diluted by filler words.

## Captured example output (real run, 2026-07-18)

**Query:** `Spi1 PU.1 knockout Csf1r expression macrophage`

Retrieved 6 real papers from Europe PMC, including:

- PMID **40673490** (2025) — *Pu.1/Spi1 dosage controls the turnover and maintenance of microglia…*
- PMID **39876004** (2025) — *Sorafenib enhanced the function of MDSCs … suppressing the PU.1-CSF1R pathway*
- PMID **41759510** (2026) — *MafB is a conserved transcriptional regulator of macrophage identity*

**Answer:**

```
Responds?   YES — differentially expressed
Direction:  down
Confidence: 0.55
Citations:  PMID 39876004
```

> *Reasoning trace (abridged):* "Abstract 4 says sorafenib inhibits macrophage
> differentiation by **suppressing the PU.1-CSF1R pathway** → PU.1 activity
> promotes CSF1R expression, so knockout likely **reduces** CSF1R (down). Only
> indirect evidence, so **moderate** confidence."

The answer is biologically correct (PU.1 is a known activator of the *Csf1r*
promoter) and the confidence is honestly **calibrated to indirect evidence** —
it commits to a direction while flagging that the abstracts give a pathway-level,
not a direct-knockout, measurement.

**Second query:** `MafB transcriptional regulation macrophage identity Csf1r`
→ `responds=YES, direction=down, confidence=0.90, citations=[41759510]`. Here the
top hit's abstract states MafB *directly regulates Csf1r* and that MafB is
required for macrophage development — so its loss lowers Csf1r. Direct
mechanistic evidence, hence the higher confidence.

**Honest-abstention behavior:** on questions whose retrieved abstracts don't
speak to the target (e.g. a long natural-language query that pulls tangential
reviews), paperclip returns `responds=false, direction=unclear, confidence≈0.1,
citations=[]` rather than hallucinating a result. Resistance to over-claiming is
part of the demonstration.

## Files

| File | Role |
|---|---|
| [`src/bio_reasoning/agents/paperclip.py`](../src/bio_reasoning/agents/paperclip.py) | Agent: Europe PMC search, prompt/parse, `answer_question` orchestration |
| [`scripts/paperclip_demo.py`](../scripts/paperclip_demo.py) | Runnable CLI demo (human + `--json` output) |
| [`tests/test_paperclip.py`](../tests/test_paperclip.py) | 8 offline unit tests (HTTP + LLM mocked) |
