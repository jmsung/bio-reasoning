"""paperclip — agentic literature-search demo (runnable).

Ask a perturbation-biology question; paperclip searches Europe PMC (open, no
auth), reads the top abstracts, and an LLM reasons over them to emit a
STRUCTURED, CITED answer: does the target respond? direction? confidence? PMIDs.

Portfolio / showcase piece — NOT a competition submission. On the challenge's
DE axis external-knowledge retrieval lands at parity, and arbitrary literature
is off the allowed-data list, so paperclip is a demonstration of clean agentic
tool-use + honest cited reasoning. See docs/paperclip-demo.md.

Usage:
    uv run python scripts/paperclip_demo.py \
        "Does knockdown of Spi1/PU.1 change Csf1r expression in macrophages, and in which direction?"

    uv run python scripts/paperclip_demo.py --top-k 6 --json "<question>"

LLM: gpt-oss-120b via OpenRouter. Key from .env.local (OPENROUTER_API_KEY);
key contents are never printed.
"""

from __future__ import annotations

import argparse
import json
import os
import textwrap
from pathlib import Path

from dotenv import load_dotenv

from bio_reasoning.agents.paperclip import (
    PaperclipResult,
    answer_question,
    make_search_fn,
    openrouter_llm_fn,
)

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.local", override=True)

MODEL = "openai/gpt-oss-120b"
DEFAULT_QUESTION = (
    "Does knockdown of Spi1/PU.1 change Csf1r expression in macrophages, " "and in which direction?"
)


def _print_human(res: PaperclipResult) -> None:
    print(f"\nQ: {res.question}\n")
    print(f"Retrieved {len(res.papers)} paper(s) with abstracts from Europe PMC:")
    for i, p in enumerate(res.papers, 1):
        print(f"  [{i}] PMID {p.pmid} ({p.year}) {p.title}")
        print(f"      {p.url}")

    print("\n--- Answer " + "-" * 40)
    if not res.parsed:
        reason = (
            "no papers with abstracts found" if not res.papers else "could not parse LLM output"
        )
        print(f"  UNRESOLVED ({reason}).")
        if res.reasoning:
            print(textwrap.indent(textwrap.fill(res.reasoning, 88), "  "))
        return

    responds = "YES — differentially expressed" if res.responds else "NO — not clearly responsive"
    print(f"  Responds?   {responds}")
    print(f"  Direction:  {res.direction}")
    print(f"  Confidence: {res.confidence:.2f}")
    cited = ", ".join(res.citations) if res.citations else "(none)"
    print(f"  Citations:  PMID {cited}")
    print("\n  Reasoning trace:")
    print(textwrap.indent(textwrap.fill(res.reasoning, 88), "    "))
    tok = int(res.tokens.get("total_tokens", 0))
    if tok:
        print(f"\n  (tokens used: {tok})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    ap.add_argument("--top-k", type=int, default=8, help="papers to retrieve + read")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--json", action="store_true", help="emit the full result as JSON")
    args = ap.parse_args()

    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("BIOREASONING_OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY not found in env (.env.local).")

    res = answer_question(
        args.question,
        search_fn=make_search_fn(),
        llm_fn=openrouter_llm_fn(api_key=api_key, model=MODEL),
        top_k=args.top_k,
        seed=args.seed,
    )

    if args.json:
        print(
            json.dumps(
                {
                    "question": res.question,
                    "responds": res.responds,
                    "direction": res.direction,
                    "confidence": res.confidence,
                    "citations": res.citations,
                    "papers": [
                        {"pmid": p.pmid, "year": p.year, "title": p.title, "url": p.url}
                        for p in res.papers
                    ],
                    "parsed": res.parsed,
                    "tokens": res.tokens,
                    "trace": res.trace,
                },
                indent=2,
            )
        )
    else:
        _print_human(res)


if __name__ == "__main__":
    main()
