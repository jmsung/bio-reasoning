---
source_url: https://github.com/tobi/qmd
source_type: repos
title: qmd — local document search engine
author: Tobias Lütke
license: MIT
retrieved: 2026-06-06
---

# tobi/qmd

**Language:** TypeScript
**License:** MIT
**Install:** `npm install -g @tobilu/qmd` (or `bunx @tobilu/qmd`)

## What it is

CLI tool that indexes and searches markdown documents, notes, and
knowledge bases **entirely on-device**. Combines BM25 + vector + LLM
re-ranking ("hybrid search") with no external API calls — runs
local GGUF models via node-llama-cpp.

## Key features

- Hybrid search pipeline: BM25 (FTS5) + vector similarity + LLM reranker
- Reciprocal Rank Fusion with position-aware blending (75% retrieval
  score for top-ranked, 60% reranking for tail)
- Markdown-aware chunking with AST-aware code parsing
- MCP support for Claude and other agents
- Output formats: JSON, CSV, Markdown, XML

## Relevant techniques

- **Hybrid retrieval**: classic IR (BM25) + dense embeddings + cross-encoder
  rerank — the standard "best of three worlds" pattern, packaged as a single CLI.
- **Position-aware RRF**: a refinement of vanilla RRF that weights
  retrieval vs. rerank scores based on rank position.
- **On-device only**: avoids the auth/latency/cost of hosted vector DBs;
  fine for personal/team-sized knowledge bases.

## Why interesting for us

`/wiki-query` (in `.claude/skills/`) uses qmd as its preferred search
backend when available, falling back to grep. Register a collection
once (`qmd collection add ./knowledge/source --name bio-reasoning`) and the
team source layer becomes semantically searchable. Optional, personal
— not a team dependency.

## Usage

```bash
qmd collection add ~/notes --name notes
qmd context add qmd://notes "Personal notes and ideas"

qmd search "keyword"       # BM25 only (fastest)
qmd vsearch "concept"      # vector only
qmd query "hybrid search"  # full pipeline (best quality)
```
