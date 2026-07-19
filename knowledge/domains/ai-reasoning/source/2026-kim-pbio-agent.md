---
distilled_from: raw/2026-kim-pbio-agent.md
distilled_from_hash: 6996cfa65a75
distilled_at: 2026-07-06
status: distilled
source_type: papers
source_url: https://openreview.net/forum?id=5GIEGTv9y4
code_url: https://github.com/icecream126/pbioagent_lincsqa
project_page: https://icecream126.github.io/LINCSQA_PBIOAGENT_project_page/
title: Progressive Multi-Agent Reasoning for Biological Perturbation Prediction
author: Hyomin Kim, Sangyeon Hwang, Jaechang Lim, Yinhua Piao, Yunhak Oh, Woo Youn Kim, Chanyoung Park, Sungsoo Ahn, Junhyeok Jeon
retrieved: 2026-07-06
---

# Progressive Multi-Agent Reasoning for Biological Perturbation Prediction

**Venue:** ICML 2026 Workshop (Generative and Agentic AI for Biology), poster
**Groups:** KAIST (Woo Youn Kim / Sungsoo Ahn / Chanyoung Park labs)

> Paper PDF is behind an OpenReview verification wall; this page is distilled
> from the project page, the ICML abstract, and the public GitHub README.

## Abstract

Introduces **LINCSQA** (benchmark) + **PBio-Agent** (training-free multi-agent
framework) for LLM-based gene-regulation-under-perturbation prediction. Core
insight: genes hit by the same perturbation share causal structure, so
confidently-predicted genes can contextualize harder ones (a curriculum). It is
the first benchmark for *bulk-cell chemical* perturbation (LINCS L1000, 20k+
compounds), in contrast to prior *single-cell genetic* work.

## Key contributions

- **LINCSQA**: gene-regulation-direction (up/down) QA plus an MoA-plausibility
  task, spanning 8 organs / cell lines, constructed from the LINCS L1000
  perturbation database.
- **PBio-Agent**: 3 Scientist agents (Context, Mechanism, Network) + 1
  Integration agent (with optional GAT predictions) + 4 Judge agents
  (History-Leakage, Target-Verifier, Consistency, Logic) + retry logic. No
  model training required.
- **Difficulty-aware curriculum**: order genes by LLM confidence and STRING
  relatedness, then use confident predictions to condition harder cases
  (iterative knowledge refinement).

## Methods

Runs an open-weights LLM (default DeepSeek-R1-Distill-Llama-8B) served via
VLLM. Two tasks: Task1 = gene regulation direction prediction (optional GAT
integration, AUROC/accuracy per organ); Task2 = MoA case studies (BRAF, KRAS)
with an `--allow_uncertain` option. Pipeline: scientist agents reason →
integration agent synthesizes (± GAT) → judge agents validate → retry on
failure.

## Key results

- 8B model reaches **0.81 AUROC on skin**, best across 7/8 tissue types, and
  **outperforms 32B baselines**.
- Mechanistic MoA reasoning correctly identifies drug-sensitive cell lines in
  BRAF/KRAS case studies.
- Reports **SOTA on PerturbQA** (genetic single-cell) — our existing baseline
  [[2025-wu-perturbqa]].

## Why interesting (for us)

- A directly beatable and borrowable baseline: the agent scaffold is reusable,
  runs on a cheap 8B model, and the code is public. Relevant to the
  perturbation + MoA framing across Tracks A/B/C
  [[2026-bioreasoning-challenge-overview]].
- **Caveat:** LINCSQA is chemical / bulk-cell (L1000), whereas our PerturbQA
  work is genetic / single-cell — the scaffold transfers, the data differs.
- Repo layout: `run.py` entry point; `utils/{agents,judges,orchestrator,
  llm_client,pipeline_data_loader}`; `metrics/gene_regulation_prediction.py`
  for AUROC; GAT checkpoints under `checkpoints/`.

## Limitations / open questions

- Bulk-cell chemical setting differs from most single-cell genetic benchmarks;
  transfer of the curriculum idea to single-cell (our setting) is untested here.
- Judge/retry adds LLM calls — cost vs accuracy tradeoff not quantified in the
  public materials.
- Full quantitative tables require the gated PDF; numbers above are from the
  project page / abstract.
