<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: bio-foundation-models
domains: [bio-foundation-models, bio-multiomics]
title: "CellBench-LS: Benchmark Evaluation of Single-cell Foundation Models for Low-supervision Scenarios"
authors: [Xu et al.]
year: 2026
doi: 10.64898/2026.04.01.714123
source_url: https://www.biorxiv.org/content/10.64898/2026.04.01.714123v1
drive_file_id: TODO
text_source: web
ingested_by: agent
---
# CellBench-LS: Benchmark Evaluation of Single-cell Foundation Models for Low-supervision Scenarios

**Authors:** Yongjie Xu, Yiyun Li, Yue Yuan, Chang Yu, Zelin Zang
**Year:** 2026
**Venue:** bioRxiv (doi:10.64898/2026.04.01.714123)

## Abstract
Single-cell foundation models (SCFMs) show promise across downstream tasks, but their generalization in label-scarce settings is a critical bottleneck and lacks systematic benchmarks. CellBench-LS is a framework that rigorously evaluates SCFM generalization under low-supervision conditions using a stratified protocol comparing traditional methods and foundation models. Zero-shot representational ability is assessed on clustering and batch correction; lightweight fine-tuning of task-specific heads is used for cell-type annotation, expression reconstruction, and perturbation prediction. Results reveal a biologically stratified landscape: foundation models excel at tasks reliant on cell-type recognition, while traditional methods remain competitive when precise quantification of gene expression is required.

## Key contributions
- First benchmark to systematically compare 7 SCFMs against classical baselines across 5 tasks under **both zero-shot and few-shot** low-supervision settings (prior benchmarks were zero-shot-only or single-task).
- Stratified protocol: frozen embeddings for unsupervised tasks; uniform MLP heads with identical training config for supervised tasks, so differences trace to representations, not implementation.
- Practical model-selection guidance keyed to task type and data scale.

## Methods
- **Models (7 SCFMs):** scGPT, Geneformer, LangCell, CellPLM, scMulan, scFoundation, Nicheformer. **Classical baselines:** PCA, UMAP, scVI. All use public checkpoints + official preprocessing.
- **Tasks:** clustering (zero-shot; ARI/NMI/ASW, Louvain), batch correction (zero-shot; iLISI/cLISI/cASW, Harmony), cell-type annotation (few-shot k=1,3,5,7,9; accuracy/Macro-F1), gene expression reconstruction (few-shot k=100–900; MSE/Pearson on top-400 genes), **perturbation prediction** (few-shot k=1,3,5,7,9 pairs/perturbation; concatenate cell embedding with a perturbation-gene vector → MLP predicts post-perturbation profile; DES/MAE).
- **Data:** 13 scRNA-seq datasets (general, multi-batch, perturbation). Perturbation uses **Adamson and Norman** CRISPR-screen datasets.

## Key results
- **CellPLM and Nicheformer are the strongest SCFMs overall** — top-tier on clustering, batch correction, annotation, and reconstruction. LangCell and Geneformer are the weakest for clustering.
- **Annotation & perturbation (few-shot): SCFMs clearly beat classical methods.** For perturbation, CellPLM, Nicheformer, and LangCell lead DES/MAE on both Adamson and Norman; scGPT/scVI improve at Top-1/Top-5 but **degrade at higher k and on Norman**.
- **Reconstruction is the exception:** classical PCA/scVI are competitive or better; SCFMs' pretraining objectives don't align with fine-grained expression quantification.
- **Heavy cross-dataset variability:** e.g., scFoundation is strong on PBMC12k but poor on hPancreas; CellPLM shows the opposite. No single model wins all tasks.

## Why it matters for our work
Our task is few-shot-style prediction of `(pert gene, target gene) → up/down/none` in macrophage CRISPRi, with a 55% `none` majority — structurally the paper's few-shot **perturbation prediction** task (embed cell → concat perturbation-gene vector → head → predict shift). Direct read for **Track C (fine-tune an open <10B FM)**:
- **Viable picks:** CellPLM and Nicheformer are the consistent perturbation/annotation winners and are open-weights and small enough — start here rather than scGPT/Geneformer. LangCell also lands in the top tier for perturbation.
- **Failure modes to expect:** (1) SCFMs are strong on cell-type/perturbation *recognition* but weak on precise *quantification* — reassuring for a discrete up/down/none label, less so if magnitude matters. (2) Severe domain sensitivity — a model tuned on one tissue can collapse on macrophage data, so validate on-domain before trusting. (3) Baselines (scGPT/scVI) degrade as k grows and on the harder Norman set, implying our head design and few-shot budget matter as much as the FM choice. Pairing a strong FM embedding with a lightweight MLP head (as here) is a sensible Track C baseline; PCA is a cheap sanity-check baseline that is hard to beat on quantitative sub-tasks.

## Limitations / open questions
- Pretraining/downstream **objective mismatch** (masked modeling / gene ranking) leaves SCFMs weak in zero-shot and reconstruction; authors call for task-aligned inductive biases (contrastive clustering, expression-aware reconstruction).
- Poor **domain generalization** across tissues/batches — reliability across datasets is unresolved.
- No single SCFM is SOTA across tasks; specialized or multi-task approaches may be needed.
- Perturbation evaluated only on Adamson + Norman (K562-derived CRISPR screens), not macrophage/immune contexts — external validity to our CRISPRi setting is untested.
