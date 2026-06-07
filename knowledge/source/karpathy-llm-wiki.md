---
source_url: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
source_type: web
title: LLM Wiki — a pattern for personal knowledge bases using LLMs
author: Andrej Karpathy
retrieved: 2026-06-06
---

# LLM Wiki — a pattern for personal knowledge bases using LLMs

**Source:** gist.github.com/karpathy · 2026-06-06
**Author:** Andrej Karpathy

## TL;DR

Don't treat documents as static sources to RAG over at query time.
Instead, have the LLM **incrementally build and maintain a wiki** —
a structured, interlinked markdown collection that sits between raw
sources and the user. Synthesis happens once, accumulates, and stays
current. Below ~50–100k tokens, this beats RAG on reliability and
simplicity.

## Key claims

- **Knowledge compounds.** Each new source can touch 10–15 wiki pages
  (summary, index, related entity / concept pages, log). Cross-refs
  and contradictions surface naturally.
- **Maintenance is the right division of labor.** Humans curate sources
  and ask questions; LLMs do the boring upkeep that kills human wikis
  (link fixups, consistency, conflict resolution).
- **RAG is often unnecessary at modest scale.** Pure-context with a good
  index beats RAG when total tokens fit a long-context window.
- **The schema is a config file.** A `CLAUDE.md`-style document defines
  structure, conventions, and workflows; the LLM is a disciplined
  maintainer, not a free-form chatbot.

## Three-layer architecture

| Layer | Who edits | Examples |
|---|---|---|
| **Raw sources** (immutable) | nobody | articles, papers, images, data |
| **Wiki** (LLM-generated) | LLM | summaries, entity / concept pages, overviews, log |
| **Schema** (config) | human | wiki structure, conventions, workflows |

## Workflow: Ingest → Query → Lint

- **Ingest** — drop a source; LLM reads, drafts a summary, updates index,
  revises related pages, appends to log. One source may touch 10–15 pages.
- **Query** — ask a question; LLM searches the wiki, cites, optionally
  files high-value answers back as new pages so insights compound.
- **Lint** — periodic health check: contradictions, stale claims,
  orphans, missing cross-refs.

## Supporting infrastructure

- `index.md` — content-oriented catalog; lets the LLM find pages without
  embeddings.
- `log.md` — append-only chronological record; greppable.
- Optional search backend (e.g., qmd) for larger wikis.
- Obsidian recommended as the IDE — wikilinks, graph view alongside the agent.

## Historical reference

Vannevar Bush's **Memex** (1945) — the original vision of personal,
curated knowledge with associative trails. Karpathy: *"The part he
couldn't solve was who does the maintenance. The LLM handles that."*

## Why interesting for us

Direct parallel to what we're doing in `knowledge/source/` + `knowledge/wiki/`
(ingest → query → lint via `/wiki-ingest`, `/wiki-query`,
`/wiki-lint`). Validates the pattern; also suggests refinements we
might adopt:

- **Filing query answers back into the wiki** — our `/wiki-query
  --file-back` does this; underused so far. Lands in `knowledge/wiki/findings/`.
- **The wiki touching 10–15 pages per ingest** — we currently write
  only the source distillation page; we don't auto-update related
  concept pages in `knowledge/wiki/`. Worth considering when we have more
  pages to interconnect.
- **`log.md` as append-only history** — we have one in `knowledge/wiki/`;
  check that `/wiki-ingest` is actually appending to it.

## Open questions

- When does the wiki cross the size threshold where RAG/qmd genuinely
  beats grep? Probably much later than we think.
- Does the pattern hold for a 3-person team where the wiki is shared,
  or is it really a single-author pattern? (Karpathy frames it as
  personal.)
