<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: bio-foundation-models
domains: [bio-foundation-models]
title: Rapid protein evolution by few-shot learning with a protein language model
authors: [Kaiyi Jiang, Zhaoqing Yan, Matteo Di Bernardo, Samantha R. Sgrizzi, Lukas Villiger, Alisan Kayabolen, Byungji Kim, Josephine K. Carscadden, Masahiro Hiraizumi, Hiroshi Nishimasu, Jonathan S. Gootenberg, Omar O. Abudayyeh]
year: 2024
doi: 10.1101/2024.07.17.604015
source_url: https://www.biorxiv.org/content/10.1101/2024.07.17.604015v1
drive_file_id: TODO
text_source: paperclip
ingested_by: agent
---

# Rapid protein evolution by few-shot learning with a protein language model

## TL;DR
EVOLVEpro is a few-shot active-learning framework that pairs frozen protein-language-model (PLM) embeddings with a lightweight activity regressor to guide in-silico directed evolution, reaching up to 100-fold activity improvements in as few as four experimental rounds across five diverse proteins.

## Key findings
- **Framework.** EVOLVEpro combines a PLM (for sequence embeddings) with a top-layer **protein activity predictor** trained on small amounts of experimental data, then runs **iterative active learning**: predict promising variants → measure → retrain → propose the next round. The activity model is trained few-shot rather than zero-shot.
- **Headline result.** Yields proteins with **up to 100-fold improvement** in the desired property, with measurable gains in **as few as four rounds** of evolution — substantially fewer experiments than conventional directed evolution.
- **Generalization claim.** Positioned against prior PLM-guided approaches that "fail to generalize across diverse protein families"; EVOLVEpro is demonstrated on **five proteins spanning three application areas**, arguing the few-shot active-learning loop generalizes where zero-shot PLM scoring does not.
- **Demonstrated proteins / applications:**
  - **T7 RNA polymerase** — improved RNA production.
  - A **miniature CRISPR nuclease** — genome editing.
  - A **prime editor** — genome editing.
  - An **integrase** — genome editing.
  - A **monoclonal antibody** — improved epitope binding.
- **Central methodological claim.** Few-shot learning on small experimental datasets outperforms **zero-shot PLM predictions** and beats current state-of-the-art in-silico evolution methods, while avoiding the labor and local-maxima trapping of wet-lab-only directed evolution.
- **Multi-property motivation.** The authors frame existing directed-evolution methods as unable to efficiently optimize over multiple protein properties simultaneously and prone to local maxima — gaps the active-learning loop is designed to address.

## Methods (brief)
The system uses pretrained PLM embeddings as fixed features fed to a supervised activity predictor; an active-learning acquisition step selects the next variants to assay experimentally, and the predictor is retrained each round on the accumulated labels. Each of the five case-study proteins is coupled to an application-specific functional assay (RNA yield, editing efficiency, integration, antibody binding) used to generate the round-by-round activity labels.

## Limitations
Distillation is based on the abstract only (Introduction/Discussion sections were not retrievable from the source extraction; original PDF was Cloudflare-blocked), so specific per-protein fold-changes, round counts, baselines, and acquisition-function details could not be verified beyond the headline "up to 100-fold" and "as few as four rounds." Results depend on having a quantitative, reasonably high-throughput activity assay per target, and the generalization claim rests on five proteins.

## Citations of interest
- Protein language models (e.g. ESM family) — source of the sequence embeddings underpinning the activity predictor.
- Prior zero-shot PLM variant-effect prediction methods — the baseline EVOLVEpro argues it surpasses.
- Directed-evolution literature — the wet-lab paradigm being accelerated/replaced.

(Specific reference list not recoverable from the available extraction.)
