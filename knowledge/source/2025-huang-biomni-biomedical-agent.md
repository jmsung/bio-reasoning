---
source_url: https://doi.org/10.1101/2025.05.30.656746
source_type: papers
title: "Biomni: A General-Purpose Biomedical AI Agent"
author: Kexin Huang et al.
retrieved: 2026-07-16
doi: 10.1101/2025.05.30.656746
---

# Biomni: A General-Purpose Biomedical AI Agent

**Authors:** Kexin Huang, Serena Zhang, Hanchen Wang, Yuanhao Qu, Yingzhou Lu, Yusuf Roohani, Ryan Li, Lin Qiu, Gavin Li, Junze Zhang, Di Yin, Shruti Marwaha, Jennefer N. Carter, Xin Zhou, Matthew Wheeler, Jonathan A. Bernstein, Mengdi Wang, Peng He, Jingtian Zhou, Michael Snyder, Le Cong, Aviv Regev, Jure Leskovec
**Year:** 2025
**Venue:** bioRxiv (preprint)

## Abstract
Biomni is a general-purpose biomedical AI agent designed to autonomously execute a wide spectrum of research tasks across diverse subfields. An action-discovery agent mines tools, databases, and protocols from tens of thousands of publications spanning 25 biomedical domains to build the first unified agentic environment. On top of this, a generalist architecture integrates LLM reasoning with retrieval-augmented planning and code-based execution, letting Biomni dynamically compose complex workflows without predefined templates. Systematic benchmarking shows strong zero-shot generalization across heterogeneous tasks — causal gene prioritization, drug repurposing, rare disease diagnosis, microbiome analysis, molecular cloning — with no task-specific prompt tuning. It is deployed at biomni.stanford.edu.

## Key contributions
- An AI-driven action-discovery pipeline that mines the biomedical action space from 2,500 recent bioRxiv papers across 25 subfields, curated by experts into 105 software tools, 150 specialized biological tools, and 59 databases.
- A generalist agent (Biomni-A1) built on the CodeAct framework: LLM plan → prompt-based retriever selects relevant tools/data → iterative code execution (Python/R/Bash) with observation feedback.
- Eight new real-world biomedical benchmarks (genetics, genomics, microbiology, pharmacology, clinical) plus a wet-lab-validated molecular cloning study.

## Methods
Given a query, Biomni prompts the LLM (Claude Sonnet 3.7 in experiments) to produce a numbered plan, then a separate LLM-powered retriever dynamically selects the relevant functions, datasets, and software to avoid long context. The LLM generates code, executes it in an interactive environment, and feeds observations back until convergence. Baselines: base LLM (no tools), ReAct+Code (coding agent), and Biomni-ReAct (ablation replacing code-based planning with ReAct-style chaining). Benchmarks were curated from Open Target Genetics, GWAS loci, CRISPR screens (Schmidt et al.), MyGene2 rare-disease data, drug-repurposing EHR alignment, and multiple microbiome datasets.

## Key results
- LAB-Bench DbQA: 74.4% accuracy, matching expert humans (74.7%) and beating ReAct+Code (40.8%).
- LAB-Bench SeqQA: 81.9%, exceeding human level (78.8%).
- Humanity's Last Exam (biomedical subset): 17.3% vs base LLM 6.0%, coding agent 12.8%, literature agent 12.2%.
- Across the 8 real-world tasks: average relative gain of 402.3% over base LLM, 43.0% over ReAct+Code, 20.4% over its own Biomni-ReAct ablation — underscoring code-centric planning + environment grounding.
- Molecular cloning: Biomni matched a senior human expert in accuracy/completeness (5-point rubric), beat trainee humans, in a fraction of the time; a Biomni-designed sgRNA cloning protocol was wet-lab validated (colonies + perfect Sanger alignment).

## Why it matters for our work
Biomni's benchmark suite directly overlaps our problem space: GWAS causal-gene detection, variant prioritization, and CRISPR perturbation screen design are close cousins of the BioReasoning Challenge Track A/B gene-perturbation prediction. Its central finding — that code-based planning plus a grounded tool/data environment beats a bare LLM by ~4x and beats ReAct-style chaining by ~20% — is a strong prior for our own agentic Track B system (our jsagent), which under-performed partly from over-abstention and thin tooling. The retrieval-augmented tool selection and iterative code-execution loop are a concrete architecture to borrow. It also uses Claude Sonnet as the reasoning backbone, matching our local dev fallback.

## Limitations / open questions
- Benchmarks use small subsets (e.g., 12.5% of LAB-Bench, 52-question HLE subset) due to API cost; the paper itself flags the HLE subfield breakdown as possibly not meaningful.
- Absolute HLE accuracy is low (17.3%) — open-ended biomedical reasoning remains hard.
- Performance depends on the underlying LLM (Claude 3.7) and a large curated tool/database environment; unclear how it transfers to open-weights models like our Track C GPT-OSS setup.
- Cloning and case studies are single-instance, expert-reviewed demonstrations rather than large-scale quantitative evaluation.
