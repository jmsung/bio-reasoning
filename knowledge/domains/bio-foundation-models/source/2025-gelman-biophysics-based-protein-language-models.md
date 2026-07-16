<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: bio-foundation-models
domains: [bio-foundation-models]
title: Biophysics-based protein language models for protein engineering
authors: [Sam Gelman, Bryce Johnson, Chase R. Freschlin, Arnav Sharma, Sameer D'Costa, John Peters, Anthony Gitter, Philip A. Romero]
year: 2024
doi: 10.1038/s41592-025-02776-2
source_url: https://doi.org/10.1038/s41592-025-02776-2
drive_file_id: TODO
text_source: paperclip
ingested_by: agent
---

# Biophysics-based protein language models for protein engineering

## TL;DR
METL (mutational effect transfer learning) pretrains transformer protein language models on millions of Rosetta biophysical simulations rather than evolutionary sequences, then fine-tunes on sparse experimental sequence–function data — excelling at low-data and extrapolation tasks and designing functional GFP variants from only 64 training examples.

## Key findings
- **Core idea:** replace evolutionary pretraining (ESM, UniRep) with *synthetic biophysical* pretraining. Generate millions of sequence variants (≤5 substitutions), model each structure with Rosetta, extract 55 biophysical attributes (vdW, solvation, H-bonding, surface areas), and train a transformer encoder to predict them. Then fine-tune on experimental data.
- **Two scales:** METL-Local (~2.5M params) pretrains on ~20M variants around one protein of interest; METL-Global (~20M params) pretrains on ~30M variants across 148 diverse base proteins for a general representation.
- **Pretraining accuracy:** METL-Local recapitulates Rosetta total score at mean Spearman 0.91 (across 8 source models). METL-Global hits 0.85 in-distribution but only 0.16 out-of-distribution — it overfits the 148 base proteins, yet still learns transferable embeddings.
- **Generalization (11 deep-mutational-scanning datasets: GFP, GB1, TEM-1, PTEN, DLG4, GRB2, Pab1, Ube4b):** protein-specific models (METL-Local, Linear-EVE, ProteinNPT) beat general models (METL-Global, ESM-2) on small training sets. METL-Local is strongest on GFP and GB1.
- **Extrapolation tasks:** mutation extrapolation ~0.70–0.78 across top methods; **position extrapolation** — the hardest, requiring structural priors — led by ProteinNPT (0.65) and METL-Local (0.59), where local pretraining (all mutations at all positions) gives comprehensive prior knowledge. Score extrapolation (low→high fitness) was hard for all (<0.3 most datasets; GB1 exception with METL >0.7).
- **Simulated vs experimental data trade-off (GB1):** ~29 simulated data points ≈ 1 experimental data point. Diminishing returns set in at ~16,000–128,000 simulated examples — far below the 20M used, so much less simulation could suffice.
- **Structure-aware architecture:** a 3D structure-based relative position embedding (Cβ contact graph, clipped at 3 hops) makes pretrained attention maps mirror the residue distance matrix; a 1D sequence-only embedding does not. Residue representations cluster by relative solvent accessibility — structural understanding emerges before any experimental data (Extended Data Fig. 1).
- **Function-specific pretraining (METL-Bind):** adding 17 GB1–IgG complex binding scores (72 total tasks) improved fine-tuned prediction at the binding interface, notably at Glu27 — function-tailored simulations sharpen the representation.
- **GFP design (wet-lab validated):** fine-tuned on only 64 variants, METL designed 20 GFP variants via simulated annealing. **16/20 were fluorescent.** "Observed AA" designs hit 100% (5/5 at both 5 and 10 mutations); harder "Unobserved AA" (forcing mutation/position extrapolation) hit 80% (5-mut) and 40% (10-mut). Random baselines were essentially non-fluorescent.

## Methods (brief)
Rosetta v3.13 (ref2015 + centroid score3 + custom filter terms) computed 55 attributes per variant via FastRelax; ~37–215 s/variant orchestrated on the Open Science Pool via HTCondor. Transformer encoders use relative position embeddings (Shaw et al.), pre-layer-norm, global average pooling. Fine-tuning is dual-phase (head then full backbone at reduced LR). Baselines: Rosetta total score, EVE, RaSP, Linear, Linear-EVE, ProteinNPT, ESM-2. GFP designs validated as mKate2 fusion fluorescence ratios in E. coli.

## Limitations
METL-Global overfits its 148 pretraining proteins (OOD Rosetta Spearman 0.16). Rosetta pretraining inherits Rosetta's blind spots — e.g., it underestimates disulfide-driven positive epistasis (Y3C/A26C) because Rosetta doesn't auto-model disulfides. GB1 was used as development dataset (possible optimism). No designed GFP exceeded wild-type brightness, and Unobserved 10-mutant designs were destabilized.

## Citations of interest
- Rives et al. 2021 (ESM) & Lin et al. 2023 (ESM-2) — evolutionary PLM baselines METL is contrasted against.
- Alford et al. 2017 — Rosetta ref2015 all-atom energy function, the simulation engine for pretraining data.
- Frazer et al. 2021 (EVE) and Blaabjerg et al. 2023 (RaSP) — evolutionary and Rosetta-ΔΔG stability baselines.
- Notin et al. 2023 (ProteinNPT) — non-parametric transformer, the strongest competing protein-specific method.
- Sarkisyan et al. 2016 — GFP local fitness landscape, source of the GFP DMS data and expression system.
- Olson, Wu & Sun 2014 — GB1 pairwise epistasis dataset used for the binding/epistasis analyses.
