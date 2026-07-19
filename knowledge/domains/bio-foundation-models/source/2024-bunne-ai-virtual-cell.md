---
source_url: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11468656/
source_type: papers
title: "How to Build the Virtual Cell with Artificial Intelligence: Priorities and Opportunities"
author: Charlotte Bunne et al.
retrieved: 2026-07-16
doi: n/a (PMCID PMC11468656, PMID 39398201)
---

# How to Build the Virtual Cell with Artificial Intelligence: Priorities and Opportunities

**Authors:** Charlotte Bunne, Yusuf Roohani, Yanay Rosen, Ankit Gupta, Xikun Zhang, Marcel Roed, Theo Alexandrov, Mohammed AlQuraishi, Andrea Califano, Emily B. Fox, Eric Horvitz, Patrick D. Hsu, Fabian Theis, Christina V. Theodoris, Marinka Zitnik, Theofanis Karaletsos, Aviv Regev, Emma Lundberg, Jure Leskovec, Stephen R. Quake, and colleagues (42 authors across Stanford, Genentech, CZI, Arc Institute, EPFL, Broad, and others)
**Year:** 2024
**Venue:** arXiv preprint (Chan Zuckerberg Initiative AI Virtual Cell roadmap)

## Abstract
A large multi-institution consortium lays out a vision and community roadmap for the **AI Virtual Cell (AIVC)**: a high-fidelity, learned simulator of cells and cellular systems under varying conditions (differentiation, perturbation, disease, environment) built directly from biological data across measurements and scales. The paper defines the desired capabilities of an AIVC, a proposed architecture, and the data, evaluation, and open-collaboration requirements to build one. It is a perspective/priorities piece, not an empirical benchmark — no models are trained or scored here.

## Key contributions
- Defines three core AIVC capabilities: (1) **universal representations** of biological state across species/modalities/contexts; (2) prediction of cell function, behavior, and dynamics with mechanistic insight; (3) **in silico experimentation** to generate and test hypotheses and guide data collection.
- Proposes a concrete architecture: interconnected **foundation models** producing **Universal Representations (URs)** at three physical scales (molecular, cellular, multicellular), operated on by **Virtual Instruments (VIs)** — *Decoders* (UR → human-readable output, e.g. cell type, image, drug response) and *Manipulators* (UR → altered UR, e.g. post-perturbation state).
- Frames data needs, evaluation strategy, interpretability, and open-science collaboration as first-class requirements.

## Methods
Perspective/roadmap. The authors map ML architectures to scales: LLMs/transformers for DNA/RNA/protein sequences (masked-token objectives) at the molecular scale; vision transformers, CNNs, and autoencoders for cellular imaging + transcriptomics; graph neural networks and equivariant nets for multicellular spatial organization. Manipulators are proposed as conditional generative models (diffusion / flow matching / autoregressive transformers) that predict UR transitions given a perturbation prompt, trained on high-throughput screens (Perturb-seq, optical pooled screens). Predictions are to carry calibrated uncertainty (Bayesian inference, ensembles, conformal prediction) to drive active-learning "lab-in-the-loop" data generation.

## Key results
- No quantitative results — this is a vision paper. Its outputs are a capability taxonomy, a scalable UR+VI architecture, and a call for open benchmarks.
- Notes the Short Read Archive holds >14 petabytes of sequence data, >1000× the data used to train ChatGPT, while cautioning about redundancy, diminishing returns, and strong species/ancestry biases.
- Emphasizes evaluation should prioritize generalization to unseen cell types/genetic backgrounds (e.g. cross-modal reconstruction) and the ability to generate experimentally testable hypotheses, over narrow benchmark accuracy.

## Why it matters for our work
This is the foundational framing document for the entire "virtual cell" research agenda our BioReasoning Challenge sits inside. Track A/B's perturbation-response prediction (gene up/down/none) is exactly the paper's **Manipulator** task — predicting a perturbed cell state from a baseline representation — and Track C's open-weights foundation models are candidate **Universal Representation** backbones. The paper's stance that models should predict responses to untested perturbations while accounting for cellular context directly motivates our gene-embedding + direction-fusion strategy. Its evaluation warning (favor generalization + hypothesis quality over narrow metrics) echoes our own lesson that small-CV rank scores mislead.

## Limitations / open questions
- Aspirational: proposes an architecture but validates nothing; the UR-across-scales consistency claim is untested.
- Data diversity/bias (species, disease, ancestry) and the intractable combinatorial perturbation space are flagged as unsolved.
- Interpretability vs. black-box performance trade-off left open; no concrete metric or benchmark suite is specified.
