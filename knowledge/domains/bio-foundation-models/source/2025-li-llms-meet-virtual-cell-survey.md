<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: bio-foundation-models
domains: [bio-foundation-models, bio-multiomics]
title: "Large Language Models Meet Virtual Cell: A Survey"
authors: [Krinos Li et al.]
year: 2025
doi: 10.48550/arXiv.2510.07706
source_url: https://arxiv.org/abs/2510.07706
drive_file_id: TODO
text_source: web
ingested_by: agent
---
# Large Language Models Meet Virtual Cell: A Survey

**Authors:** Krinos Li, Xianglu Xiao, Shenglong Deng, Lucas He, Zijun Zhong, Yuanjie Zou, Zhonghao Zhan, Zheng Hui, Weiye Bao, Guang Yang
**Year:** 2025
**Venue:** arXiv:2510.07706 (preprint)

## Abstract
LLMs are being used to build "virtual cells" — computational systems that represent, predict, and reason about cellular states and behaviors. This survey maps how LLMs are applied to cellular biology, organizing the field into two paradigms (LLMs as oracles vs. as agents) across three core tasks: cellular representation, perturbation prediction, and gene regulation inference. It reviews the associated models, datasets, and evaluation benchmarks, and frames three cross-cutting challenges — scalability, generalizability, and interpretability.

## Key contributions
- A unified framework splitting LLM-for-cell work into **two paradigms**: **LLMs-as-Oracles** (reactive knowledge/reasoning engines that answer queries about genes, proteins, cell states) and **LLMs-as-Agents** (autonomous planners that decompose tasks, call tools, and iterate).
- A **three-task taxonomy**: cellular representation, perturbation prediction, gene regulation inference — with the associated model families for each.
- A consolidated review of **datasets and benchmarks** used across these tasks.
- Articulation of three field-wide **challenges**: scalability, generalizability, interpretability.

## Scope / taxonomy
The survey's top-level split is by *how the LLM is used*: as an **oracle** (single-shot prediction/interpretation — the mode nearest to a prompt-only or fine-tuned predictor) or as an **agent** (multi-step tool use, planning, closed-loop reasoning). Cutting across both are three tasks. **Cellular representation** covers sequence and single-cell encoders (DNA/RNA tokenizers, single-cell expression models such as scBERT/scGPT-style architectures, protein structure models). **Perturbation prediction** covers modeling gene-expression responses to genetic/chemical perturbations (Perturb-seq, CRISPR screens), including predicting response *direction* (up vs. down), magnitude, off-target and cell-type-specific effects. **Gene regulation inference** covers TF binding, regulatory-element identification, and gene–gene networks. Datasets named include cell atlases (e.g. Tabula Muris), Perturb-seq / CRISPR-screen collections, and multi-omic integration sets; benchmarks span single-cell classification, expression prediction, and perturbation-effect evaluation.

## Key takeaways
- The oracle-vs-agent axis is the paper's main organizing idea and maps cleanly onto competition tracks: prompt-only/fine-tune ≈ oracle, tool-using pipeline ≈ agent.
- Perturbation prediction is treated as a first-class task, explicitly including **effect-direction** prediction (upregulation vs. downregulation) from CRISPR/Perturb-seq data.
- Persistent failure modes across the field: weak mechanistic grounding, poor cross-context generalization, and black-box opacity.

## Why it matters for our work
This is an orientation map for exactly our problem. Our task — predict (perturbed gene, target gene) → up / down / none in macrophage CRISPRi — is a **perturbation-prediction, effect-direction** task in the survey's taxonomy, so the perturbation-prediction section is the most directly relevant chapter to mine for methods, datasets (Perturb-seq, CRISPR screens), and baselines. The oracle-vs-agent split lines up with our tracks: **Track A (prompt-only)** and **Track C (fine-tune <10B)** sit in the *oracle* paradigm; **Track B (agentic)** is the survey's *LLMs-as-Agents* paradigm — use its agent-methods coverage (planning, tool use, closed-loop design) as a reference list. Treat this page as a jumping-off index: follow its citations into specific perturbation-prediction and gene-regulation models rather than as a source of numbers.

## Limitations / open questions
- Survey (not benchmark): it catalogs and frames the field but does not empirically compare methods head-to-head on a shared task.
- Field-level gaps it flags: predictions lack explainable links to known biology; poor generalization across cell types, species, and protocols; weak handling of temporal/dynamic perturbation responses; a gap between sequence-level understanding and systems-level cellular behavior.
- Open directions: interpretable models tied to validated regulatory mechanisms, scaling to whole-organism complexity affordably, integrating spatial/temporal/multi-omic signals, and closed-loop LLM-guided experimental design.
- Caveat for readers: some specific model names surfaced during extraction should be verified against the PDF before citing — trust the taxonomy and task framing over any single tool name.
