---
source_url: https://doi.org/10.1038/s41467-025-58699-1
source_type: papers
title: "scPRINT: pre-training on 50 million cells allows robust gene network predictions"
author: Jérémie Kalfon et al.
retrieved: 2026-07-16
doi: 10.1038/s41467-025-58699-1
---

# scPRINT: pre-training on 50 million cells allows robust gene network predictions

**Authors:** Jérémie Kalfon, Jules Samaran, Gabriel Peyré, Laura Cantini
**Year:** 2025
**Venue:** Nature Communications

## Abstract
scPRINT is a single-cell foundation model built specifically for gene network (GN) inference, pre-trained on >50 million cells (~80 billion tokens) from the CELLxGENE database spanning multiple species, diseases, and ethnicities. Using a bidirectional transformer with novel inductive biases and a multi-task pretraining objective, scPRINT outputs cell-type-specific, genome-wide gene networks by combining attention heads into a gene-by-gene matrix, and also produces zero-shot predictions on related tasks (denoising, batch-effect correction, cell/label prediction) without fine-tuning. On atlas-level benchmarks it beats prior foundation models at GN inference and, applied to a benign prostatic hyperplasia atlas, links ion exchange, senescence, and chronic inflammation.

## Key contributions
- A foundation model purpose-built for gene-network inference (not just downstream annotation), producing cell-type-specific genome-wide networks from attention heads.
- Three-task pretraining: denoising (upsampling downsampled counts via a ZINB likelihood), bottleneck learning (reconstruct expression from the cell embedding alone), and hierarchical label classification that yields disentangled per-facet embeddings (cell type, disease, sex, etc.).
- Efficiency + openness: trained at 2M–100M params (medium model = 48h on one A40 GPU); open code, weights, dataloader, and benchmarking suites BenGRN + GRnnData.
- Gene representation via frozen ESM2 protein embeddings (from UCE), enabling generalization to unseen genes/species.

## Methods
A bidirectional (BERT-style) transformer using FlashAttention2 over up to ~2200 expressed genes, with each gene encoded by an ESM2 protein embedding, a gene-location encoding, and its expression value. Custom weighted-random-sampling covers the CELLxGENE atlas. The three losses (denoising ZINB negative log-likelihood, bottleneck reconstruction, hierarchical classification, plus a contrastive term) are summed without rescaling. Networks are extracted post-hoc by selecting/averaging attention heads into a gene×gene matrix; an optional head-selection mechanism uses a small ground-truth subset (e.g. Omnipath) to pick heads. Benchmarked against scGPT, Geneformer v2, DeepSEM, and GENIE3 on Omnipath (literature) plus cell-type-specific ChIP-seq/perturb-seq ground truths (MCalla et al. hESC/mESC; genome-wide perturb-seq on K562).

## Key results
- On the Omnipath benchmark, scPRINT (Omnipath's heads) outperforms all methods on average across 26 cell types; even without head selection scPRINT beats scGPT and Geneformer v2 on EPR. scGPT and scPRINT recover 42% and 67% more connections than GENIE3 respectively.
- On cell-type-specific MCalla ground truths, scPRINT outperforms all other methods on both AUPRC and EPR. On genome-wide perturb-seq, GENIE3 leads and scPRINT is second, but scPRINT (gwps' heads) surpasses GENIE3; Geneformer v2 performs poorly.
- Zero-shot orthogonal tasks: competitive with MAGIC/KNNsmoothing2 on denoising (and better on rare cell states of 10–200 cells); 62% cell-type accuracy on the openproblems pancreas set, beating CellTypist and matching LogReg/XGBoost on macro-F1 despite not training on the test data; convincing but not SOTA batch correction (below scGEN/scVI; top among methods not using batch labels).
- Prostate BPH case study: annotates cell type/sequencer/sex/ethnicity/disease at 0.71/0.99/0.99/0.95/0.85 accuracy; denoising recovers extra differential-expression signal from a 26-cell normal B-cell group.

## Why it matters for our work
Directly relevant to Track C (foundation models) and to gene-regulation strategy underlying Tracks A/B up/down/none prediction. scPRINT is a concrete open-weights scFM candidate whose central claim — that a good learned cell model yields reliable gene-gene interactions transferable zero-shot — is exactly the mechanism we would exploit to predict perturbation direction. Its head-selection caveat is a caution for us: general databases like Omnipath often did not improve performance, ground-truth networks disagree sharply, and different heads fit different ground truths — so we should not assume one "correct" regulatory network exists, and should validate any extracted-network signal against task-specific ground truth rather than a generic reference.

## Limitations / open questions
- No perfect GN ground truth exists; AUPRC values are very low overall, and ChIP-seq/perturb-seq/literature networks disagree, so benchmark rankings are fragile and metric-dependent.
- Head selection needs high-confidence prior interactions to help; the authors recommend all-head averaging by default — the model does not, on its own, know which heads encode true biology.
- Batch correction and zero-shot cell-typing trail purpose-built/fine-tuned tools; scPRINT confuses some pancreatic endocrine subtypes.
- Capped context (~genes per cell) since attention-approximation methods degrade performance; gene embeddings frozen to preserve versatility rather than tuned for peak accuracy.
