<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: ai-reasoning
domains: [ai-reasoning, bio-multiomics]
title: Knowledge Graphs and Reasoning LLMs for Finding Simple Yet Effective Transcriptomic Perturbation Predictors
authors: [Fawkes et al.]
year: 2026
doi: 10.48550/arXiv.2606.08816
source_url: https://arxiv.org/abs/2606.08816
drive_file_id: TODO
text_source: web
ingested_by: agent
---
# Knowledge Graphs and Reasoning LLMs for Finding Simple Yet Effective Transcriptomic Perturbation Predictors

**Authors:** Jake Fawkes, Liam Hodgson, Jason Hartford
**Year:** 2026
**Venue:** arXiv:2606.08816 (cs.LG)

## Abstract
The paper tackles predicting the effect of gene knockouts/knockdowns on downstream gene expression using biological knowledge graphs (KGs) as priors. The central finding is that a deliberately simple method — K-nearest-neighbour (KNN) over a biological knowledge graph — is highly competitive for out-of-distribution perturbation prediction, matching or beating more complex learned models. The authors then show that a reasoning LLM, trained with reinforcement learning (RL) to refine which KG neighbours are used, further improves differential-expression prediction, reaching parity with state-of-the-art on the Replogle et al. (2022) cell lines. They frame this as early evidence that KG-grounded, LLM-guided reasoning can produce simple yet effective perturbation predictors.

## Key contributions
- Establishes KG-based **KNN as a strong, simple baseline** for out-of-distribution (unseen perturbation) transcriptomic prediction.
- Introduces a **reasoning LLM trained via RL** to optimize KG-neighbourhood selection, improving downstream predictions without training directly on the expression-prediction objective.
- Shows the RL-refined pipeline reaches **SOTA-equivalent** performance on established perturbation benchmarks.

## Methods
The pipeline uses a biological knowledge graph to encode relationships between genes as a structured prior. For a queried perturbation, KNN over the graph retrieves biologically similar perturbations whose measured effects serve as a prediction. On top of this, a reasoning LLM is trained with reinforcement learning to modify/curate the neighbourhood — deciding which graph neighbours to include — so that the resulting KNN prediction better matches observed differential expression. The RL signal is derived from downstream prediction quality, so the LLM learns to reason over graph structure rather than being fit directly to expression labels.

## Key results
- KG-KNN **outperforms most competing methods** on out-of-distribution perturbation tasks.
- The RL-trained reasoning LLM achieves **performance equivalent to current SOTA** on the Replogle et al. (2022) cell lines.
- Improved generalization on downstream differential-expression prediction despite no direct supervision on that task.

## Why it matters for our work
Our task is to predict, for a (perturbation gene, target gene) pair, whether a CRISPRi knockdown drives the target **up / down / none** in mouse macrophages, with **zero train/test overlap** and a **55% `none` majority baseline** — i.e. an out-of-distribution, class-imbalanced classification. This paper is directly on-point:
- **Track A (prompt-only):** its core message — a *simple* KG-neighbour lookup is a strong OOD predictor — argues for grounding prompts in explicit gene-relationship structure (pathways, regulatory edges) rather than relying on the LLM's parametric priors alone. The "simple yet effective" framing suggests high-precision, low-complexity signals beat elaborate reasoning for this regime.
- **Track B (agentic tools):** the RL-refined "LLM curates KG neighbours" loop is a template for an agent that queries a biological KG tool, retrieves analogous perturbations, and reasons over them to call up/down/none — a concrete tool-use pattern we can adapt.
- Their OOD/unseen-perturbation setting matches our zero-overlap constraint, so their KNN-vs-learned-model comparison is a useful prior on what will generalize for us.

## Limitations / open questions
- Authors call this "early signs" — validated mainly on Replogle et al. human cell lines, **not mouse macrophages**; transfer to our organism/cell-type is unproven.
- KNN/KG quality is bounded by graph coverage; genes or edges absent from the KG likely degrade to majority-class behavior — relevant given our `none` baseline.
- Directionality (up vs down vs none) granularity of their predictions vs. our 3-class scheme is unclear from the abstract; needs full-text check before adopting.
- RL training cost and reproducibility details are not in the abstract.
