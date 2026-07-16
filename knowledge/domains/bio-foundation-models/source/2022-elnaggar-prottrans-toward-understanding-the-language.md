<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: bio-foundation-models
domains: [bio-foundation-models]
title: "ProtTrans: Toward Understanding the Language of Life Through Self-Supervised Learning"
authors: [Ahmed Elnaggar, Michael Heinzinger, Christian Dallago, Ghalia Rehawi, Yu Wang, Llion Jones, Tom Gibbs, Tamas Feher, Christoph Angerer, Martin Steinegger, Debsindhu Bhowmik, Burkhard Rost]
year: 2021
doi: 10.1109/tpami.2021.3095381
source_url: https://doi.org/10.1109/tpami.2021.3095381
drive_file_id: TODO
text_source: paperclip
ingested_by: agent
---

# ProtTrans: Toward Understanding the Language of Life Through Self-Supervised Learning

## TL;DR
Six NLP transformer/auto-regressive architectures were trained on up to 393 billion amino acids of unlabeled protein sequence; the resulting embeddings, used as the sole input to small supervised models, matched MSA/evolutionary-information–based state-of-the-art on secondary-structure and localization prediction — the first protein LM (ProtT5-XL-U50) to do so without any sequence alignment.

## Key findings
- **Six LMs trained**: two auto-regressive (Transformer-XL→ProtTXL, XLNet→ProtXLNet) and four auto-encoder (BERT→ProtBert, Albert→ProtAlbert, Electra→ProtElectra, T5→ProtT5), single amino acids as tokens. Sizes from 224M (ProtXLNet) to **3B (ProtT5-XL) and 11B (ProtT5-XXL)** parameters.
- **Scale**: trained on UniRef50/100 and BFD (2.1B proteins, 393B amino acids — ~8× larger than prior protein-LM corpora, ~500× Google's Billion Word corpus). Compute: 5616 GPUs on ORNL Summit + TPU Pods up to 1024 cores; near-linear scaling to 936 nodes (Fig. 2).
- **Per-residue secondary structure (Q3)**: ProtT5-XL-U50 reached **Q3=81.4% (CASP12) and 84.8% (NEW364)**, edging the MSA-based SOA NetSurfP-2.0 (82.0 / 84.3) — the first embeddings-only method to do so (Table 3). All transformers beat the LSTM-based DeepSeqVec; ProtTXL (auto-regressive) underperformed it.
- **Per-protein tasks**: subcellular localization Q10 and membrane/soluble Q2. ProtT5-XL-U50 hit **Q10=81%** and **Q2=91%**, with the ProtT5 models beating MSA-based DeepLoc on localization (Table 4).
- **Bi-directionality matters**: uni-directional ProtTXL was consistently worst among transformers; bi-directional context (ProtXLNet, BERT-family) was crucial for protein LMs — unlike NLP where the two perform on par.
- **Samples > model size**: downstream performance correlated with number of samples seen during pre-training (Spearman ρ=0.62, Fig. 7); no consistent correlation with model size. ProtT5-XL (3B, ~5B proteins seen) beat ProtBert-BFD (420M, ~27B seen).
- **Corpus quality > raw size**: 10× larger BFD gave only ~1.1% Q3 gain over UniRef100; the **BFD-pretrain → UniRef50-refine** protocol gave the largest gains (ΔQ3 +2.8% for ProtT5-XL), likely by de-biasing away from over-represented large families.
- **LMs shine for small families**: ProtT5-XL-U50 improved most over NetSurfP-2.0 for proteins with few homologs (Neff=1), where evolutionary information is scarce (Fig. 6).
- **Speed**: ProtT5-XL embeds a human protein in ~0.12 s, the full human proteome (20,353 proteins) in **40 min** — 4–6× faster than MMseqs2 MSA generation, runnable on a single 12 GB GPU.
- **Unsupervised structure**: raw embeddings (t-SNE) separated amino acids by biophysics (charge, polarity, size, aromatic vs aliphatic), proteins by SCOPe structural class and domain of life; ProtAlbert attention heads localized zinc-finger coordinating residues (Fig. 4, Fig. 11).

## Methods (brief)
Self-supervised masked/auto-regressive pre-training of six NLP architectures on protein sequence databases (UniRef50/100, BFD), then **frozen** embeddings (last hidden layer) fed to minimal supervised heads — a 2-layer CNN for per-residue secondary structure, mean-pooling + FNN for per-protein localization/membrane. No fine-tuning of the LM (static feature extractor). Evaluated on CASP12, TS115, CB513 and a new redundancy-reduced test set (NEW364, ≤20% PIDE, 364 chains).

## Limitations
Downstream heads kept deliberately minimal and not task-optimized (proxies, not end goals); statistical gains over NetSurfP-2.0 fell within the 68% confidence interval (±0.5%). NEW364 is small (364 proteins); CASP12 smaller still. Whether LMs implicitly learn evolutionary information is left unresolved; the authors found no evidence of a performance ceiling at the time of writing.

## Citations of interest
- Rives et al. (ESM-1b, 2019/2020) — competing large transformer protein LM; outperformed all non-ProtT5 models here.
- Rao et al. TAPE (2019) — benchmark for protein transfer learning.
- Heinzinger et al. SeqVec (2019) — prior ELMo/LSTM protein LM by same lab, baseline.
- Klausen et al. NetSurfP-2.0 (2019) — MSA-based SOA for secondary structure, the bar to beat.
- Steinegger & Söding — BFD database and MMseqs2; the corpus and the MSA-speed comparator.
- Raffel et al. T5 (2019) — architecture underlying the best-performing ProtT5.
