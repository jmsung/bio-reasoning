<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: ai-reasoning
domains: [ai-reasoning, bio-multiomics]
title: "Plausibility Is Not Prediction: Contrastive Evidence for LLM-Based Cellular Perturbation Reasoning"
authors: [Yuan et al.]
year: 2026
doi: 10.48550/arXiv.2606.01042
source_url: https://arxiv.org/abs/2606.01042
drive_file_id: TODO
text_source: web
ingested_by: agent
---
# Plausibility Is Not Prediction: Contrastive Evidence for LLM-Based Cellular Perturbation Reasoning

**Authors:** Xinyu Yuan, Xixian Liu, Jianan Zhao, Yashi Zhang, Hongyu Guo, Jian Tang (Mila – Québec AI Institute, Université de Montréal, HEC Montréal, University of Ottawa, National Research Council of Canada, CIFAR AI Chair)
**Year:** 2026
**Venue:** arXiv preprint (cs.LG), arXiv:2606.01042v1, submitted 2026-05-31

## Abstract
This paper challenges the assumption that plausible biological reasoning is sufficient for accurate cellular perturbation prediction. The authors show that current LLM-based methods, despite generating credible, biologically plausible explanations, fail to capture perturbation-specific effects. LLMs exhibit a systematic positive-prediction (over-differential-expression) bias and near-chance per-gene performance, often underperforming simple baselines. The core diagnosis is that existing approaches score each perturbation–gene pair in isolation, lacking comparative context. The proposed fix, CORE (Contrastive Organization of Relational Evidence), reframes the task as a comparison by organizing evidence around positive and negative outcomes from related perturbations drawn from biomedical knowledge graphs.

## Key contributions
- Contrastive-evidence diagnosis: LLMs produce plausible explanations but predictions that are systematically biased and near chance at the per-gene level.
- Quantifies the bias: a representative LLM baseline (VCWorld) predicts "yes" (differentially expressed) for 92.1% of queries despite only a 29.0% true-positive rate (Tahoe100M C32).
- CORE method: restructures single-pair scoring into a contrastive task using positive/negative reference perturbations retrieved from knowledge graphs.
- Two CORE variants: CORE-Reasoning (LLM reasons over contrastive evidence) and CORE-Voting (aggregation over retrieved neighbors).

## Methods
The authors evaluate LLM perturbation predictors on standard benchmarks (PerturbQA cell lines, Tahoe100M, drug-perturbation data) and audit their calibration and per-gene discriminative power, revealing that "plausibility" of the generated explanation is decoupled from predictive accuracy. CORE then supplies comparative context: for a query perturbation–gene pair, it retrieves related perturbations with known positive and negative outcomes via biomedical knowledge graphs and organizes them as contrastive evidence, so the model classifies by comparison rather than in isolation. CORE-Voting aggregates neighbor outcomes; CORE-Reasoning prompts the LLM to reason over the assembled contrastive set.

## Key results
- CORE-Voting raises macro-per-gene AUROC from chance (0.500) to 0.574 (fixed budget) / 0.627 (full support); up to 0.703–0.711 across four PerturbQA cell lines.
- CORE-Reasoning (Qwen3.5-9B) improves aggregate metrics by 26.0% AUROC, 19.8% accuracy, and 28.6% F1 on drug data.
- Baseline LLMs default to over-predicting differential expression (e.g., 92.1% "yes" vs 29.0% true positives), confirming plausible-but-wrong behavior.

## Why it matters for our work
This is a **cautionary** paper directly on our task shape: predicting a perturbation's effect on target genes. Track A/B ask us to call `(pert gene, target gene) → up/down/none` for CRISPRi knockdowns in mouse macrophages, where `none` is the 55% majority class. This paper's central warning is that LLMs generate biologically plausible rationales yet systematically **over-call differential expression** — exactly the failure mode that would hurt us against a `none`-heavy label distribution. It argues against trusting prompt-only LLM reasoning (Track A) at face value and validates our abstain/majority-baseline instincts: a model that "sounds right" can lose to a naive `none` predictor. It also points to a concrete lever for Track B (agentic): supply **contrastive context** — related perturbations with known up/down/none outcomes — rather than scoring each pair in isolation, and consider voting/aggregation over retrieved neighbors as a calibration guardrail. Given zero train/test overlap in our setup, its knowledge-graph-retrieval framing is a candidate agentic tool.

## Limitations / open questions
- CORE depends on biomedical knowledge-graph coverage for retrieving positive/negative reference perturbations; sparse or biased graphs may not transfer to mouse-macrophage CRISPRi.
- Gains are largely from contrastive framing correcting bias, not from demonstrated perturbation-specific mechanistic reasoning — open whether the model "understands" or just recalibrates.
- Benchmarks are human/drug cell lines (PerturbQA, Tahoe100M); generalization to our organism/assay and to the three-way up/down/none label (vs binary DE yes/no) is untested.
- No zero-overlap regime like ours is directly evaluated.
