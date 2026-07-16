<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: bio-foundation-models
domains: [bio-foundation-models]
title: "Ankh: Optimized Protein Language Model Unlocks General-Purpose Modelling"
authors: [Ahmed Elnaggar, Hazem Essam, Wafaa Salah-Eldin, Walid Moustafa, Mohamed Elkerdawy, Charlotte Rochereau, Burkhard Rost]
year: 2023
doi: 10.48550/arXiv.2301.06568
source_url: https://doi.org/10.48550/arXiv.2301.06568
drive_file_id: TODO
text_source: paperclip
ingested_by: agent
---

# Ankh: Optimized Protein Language Model Unlocks General-Purpose Modelling

## TL;DR
Ankh is a general-purpose encoder–decoder protein language model (PLM) that beats the prior state of the art (ESM-2 15B, ProtT5-XL-U50) on structure/function benchmarks while using <10% of pre-training parameters, ~7% of inference parameters, and ≤30% of the embedding dimension — arguing that protein-specific, knowledge-guided optimization beats brute-force scale.

## Key findings
- **Performance-per-parameter, not scale.** Ankh (large) raised the PLM SOTA average benchmark performance by **4.8%** and Ankh base by **3.4%**, despite <10%/<3% of training parameters and 30%/15% of the embedding dimension respectively (Fig. 1). ESM-2 (15B) did *not* consistently beat smaller ESM models and gave inconsistent cross-run results — direct evidence that "bigger PLM" ≠ "better PLM" on all tasks.
- **Two released models.** *Ankh* (large): 1536 embedding dim, 16 attention heads, 48-layer encoder / 24-layer decoder. *Ankh base*: 768 dim, 12 heads, same layer split. Both T5-style encoder–decoder, Gated-GELU activation, relative positional embeddings (offset 128, dim 64), pre-trained on UniRef50 (Table 11).
- **Compute/storage win.** ESM-2 (15B) needs **4× A100 80GB** for feature extraction vs. a **single A100 40GB** per Ankh model; it costs 2.0–2.2× (min) to 7.1–11.7× (max, at 1024 residues) the feature-extraction time of Ankh / Ankh base (Fig. 1c).
- **Benchmark sweep (Table 1).** Ankh leads on secondary structure (CASP12 Q3 83.8%), contact prediction (ProteinNet L/1 49.0% via embeddings), fold prediction (61.1%), EAT (71.7% mean over CATH C/A/T/H), fluorescence (Spearman 0.62), solubility (76.4%), GB1 fitness (0.84), localization (83.2%). **Embedding-based** contact prediction beat **attention-based** for all models — Ankh promotes embeddings over attention maps as the transfer-learning signal.
- **Knowledge-guided design via 23 ablations.** Single-variable experiments over masking, architecture, positional embedding, weight tying, and dataset. Winners: **1-gram span partial de-masking** (Exp. 4), **20% masking probability** (Exp. 8, chosen over 15%/30% for generalization), **48/24 encoder-heavy** layer split (Exp. 11), and relative positional embedding offset 128 / dim 64 (Exp. 20). Weight tying and UniRef90 did *not* help; UniRef50's lower redundancy beat UniRef90/UniRef100/BFD.
- **Variant generation.** High-N: auto-regressive fine-tuning (decoder-only training, frozen encoder) on malate dehydrogenase reproduced the natural MSA Shannon-entropy profile (MSE 0.10/0.09/0.08 at temperature 1.0/1.5/2.0) using <3% of the 16,706 natural sequences; >95% of generated variants were unique. Higher temperature (2.0) recovered rare CATH functional families absent at low temperature. One-N: MLM inference at 40–50% masking generated variants with low sequence identity but RMSD <1.5 Å (ColabFold-predicted) vs. the parent.

## Methods (brief)
T5-style encoder–decoder transformers trained on Google TPU v4 Pods (64/128 cores) with Flax/JAX. Downstream tasks used a frozen-embedding + ConvBERT supervised head (kernel 7, 4 heads, Gated-GELU) across TAPE/FLIP/DeepLoc/ProteinNet/NetSurfP datasets. Generation evaluated via Shannon entropy vs. MSA, BioPython global-alignment identity, CATH domain annotation, and ColabFold structure RMSD.

## Limitations
Ablations were trained for only 2 epochs, so "best" per variable was a heuristic (no single globally optimal config existed); changing the activation function confounded the depth/width and embedding-dimension optima. Benchmarks are standard public sets, not myosin-specific; generation validated on MDH and SARS-CoV-2 nanobodies, not cardiac/motor proteins.

## Citations of interest
- Lin et al. (ESM-2, bioRxiv 2022) — the up-scaling SOTA (15B params) Ankh undercuts on compute and matches/beats on accuracy.
- Elnaggar et al. (ProtTrans/ProtT5, 2020) — prior encoder–decoder PLM baseline; source of the UniRef50 > UniRef100/BFD and CNN-head findings Ankh builds on.
- Raffel et al. (T5, JMLR 2020) — the text-to-text encoder–decoder + relative positional embedding architecture adapted here.
- Hesslow et al. (RITA, 2022) & Nijkamp et al. (ProGen2, 2022) — scaling-law PLMs whose "bigger is better" premise the paper challenges.
- Repecka et al. (ProteinGAN, Nat. Mach. Intell. 2021) — source of the MDH dataset and the generative-variant comparison point.
