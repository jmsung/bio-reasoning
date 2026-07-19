---
source_url: https://doi.org/10.1093/bioinformatics/btae267
source_type: papers
title: "Topological benchmarking of algorithms to infer gene regulatory networks from single-cell RNA-seq data"
author: Marco Stock et al.
retrieved: 2026-07-16
doi: 10.1093/bioinformatics/btae267
---

# Topological benchmarking of algorithms to infer gene regulatory networks from single-cell RNA-seq data

**Authors:** Marco Stock, Niclas Popp, Jonathan Fiorentino, Antonio Scialdone
**Year:** 2024
**Venue:** Bioinformatics (Oxford)

## Abstract
Many algorithms infer gene regulatory networks (GRNs) from single-cell RNA-seq, but prior benchmarks only score whether pairwise gene-gene edges are recovered, not whether inferred networks preserve *structural* (topological) properties—which govern robustness to perturbation and the presence of hub master regulators. The authors introduce STREAMLINE, a three-step benchmarking pipeline that quantifies how well GRN algorithms capture network topology and identify hubs, using both simulated data (hundreds of networks across four topology classes) and experimental data from three organisms (yeast, mouse, human). Applying it to four top inference algorithms, they give per-property guidance on algorithm choice and expose systematic algorithm-specific biases.

## Key contributions
- STREAMLINE pipeline: (1) simulate scRNA-seq from networks of known topology via BoolODE, (2) run GRN inference, (3) score edge recovery *and* topological fidelity. BEELINE-compatible; code and data public (GitHub / Zenodo).
- Evaluates topology in three groups: **information-exchange efficiency** (Global/Local Efficiency, Average Shortest Path Length—proxies for robustness), **hub topology** (Assortativity, Clustering Coefficient, Centralization), and **hub identification** (Betweenness, Degree, Radiality, PageRank centralities).
- Shows edge-prediction skill does not transfer to topology skill.

## Methods
Four network classes span the topology space: Random (Erdős–Rényi control), Small-World, Scale-Free, and Semi-Scale-Free (out-degree power-law, uniform in-degree—models real GRNs), plus curated sub-networks of known GRNs. BoolODE converts each network to Boolean-rule ODEs and stochastically simulates ~100-cell scRNA-seq datasets. Four algorithms chosen as top BEELINE performers are benchmarked: **PIDC** and **PPCOR** (undirected), **SINCERITIES** and **GRNBoost2** (directed, converted to undirected). The top-k edges (k = ground-truth edge count) form the evaluated graph. Graph properties are scored by MSE against ground truth; hub identification is scored by the Jaccard coefficient of top-10% hub nodes normalized against a random predictor (J/J_rand). Scores are max-scaled per metric and aggregated into an overall topology score.

## Key results
- **No single winner**—the best algorithm depends on the target property and the data. On synthetic data, **PPCOR** wins overall across all three topology tasks; SINCERITIES is best for Average Shortest Path Length, and GRNBoost2 is best for Assortativity, Centralization, and PageRank.
- On experimental data, **GRNBoost2** best identifies hubs, **SINCERITIES** best captures information-exchange and hub-topology metrics, and **PIDC** best estimates Local Efficiency and Clustering Coefficient.
- Global Efficiency is estimated well by all (average per-type MSE ~3% of ground truth), but algorithms show consistent direction-of-error biases: SINCERITIES overestimates Global Efficiency and produces overly disassortative/centralized networks; GRNBoost2 and PPCOR underestimate efficiency.
- Topology-prediction performance correlates only weakly or non-significantly with edge-prediction performance—recovering edges well does not guarantee recovering structure.

## Why it matters for our work
The BioReasoning Challenge asks systems to reason about gene regulation and predict perturbation outcomes (Track A/B up/down/none). This paper is a caution and a design input: a GRN that scores well on pairwise edges can still misrepresent the network structure that actually drives perturbation propagation and identifies master-regulator hubs—exactly the signal a perturbation-direction predictor needs. If we build or consume an inferred GRN as a reasoning scaffold, we should pick the inference method by the topological property we depend on (hub identification vs. robustness) rather than by edge AUROC, and treat algorithm-specific structural biases as a known failure mode.

## Limitations / open questions
- Only four inference algorithms; directed-network information is largely collapsed to undirected for comparability.
- BoolODE-simulated data may not capture real scRNA-seq noise/dropout, and "ground-truth" experimental GRNs are themselves silver standards.
- Mechanistic causes of the observed algorithm biases (e.g., SINCERITIES' Granger-causality false positives) are speculated, not proven.
