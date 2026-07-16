<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: bio-foundation-models
domains: [bio-foundation-models]
title: Fast and accurate protein structure search with Foldseek
authors: [van Kempen M, Kim SS, Tumescheit C, Mirdita M, Lee J, Gilchrist CLM, Söding J, Steinegger M]
year: 2023
doi: 10.1038/s41587-023-01773-0
source_url: https://doi.org/10.1038/s41587-023-01773-0
drive_file_id: TODO
text_source: paperclip
ingested_by: agent
---

# Fast and accurate protein structure search with Foldseek

## TL;DR
Foldseek reduces protein structure comparison to fast sequence alignment by encoding each residue's tertiary interactions as a learned 20-state structural alphabet (3Di), achieving 4–5 orders of magnitude speedup over Dali/TM-align/CE while retaining 86%/88%/133% of their respective sensitivities.

## Key findings
- **3Di alphabet.** Rather than discretizing backbone conformation (like CLE, 3D-BLAST, Protein Blocks), Foldseek describes, for each residue *i*, the geometric conformation of its tertiary interaction with its spatially closest residue *j*. A "virtual center" (optimized at θ=270°, τ=0°, l=2) selects the nearest neighbor, preferring long-range tertiary contacts. Ten features (7 angles, Cα distance, 2 sequence-distance features) are discretized into 20 states by a VQ-VAE (492 trainable parameters) trained to maximize evolutionary conservation, not generative reconstruction.
- **Three advantages of 3Di** over backbone alphabets: weaker dependency between consecutive letters, more evenly distributed state frequencies (both raise information density and cut false positives), and highest information density in conserved cores (opposite of backbone alphabets).
- **Pipeline** reuses MMseqs2: discretize → double-diagonal k-mer + ungapped prefilter on 3Di sequences → SIMD Smith–Waterman local alignment combining 3Di and amino-acid scores (weights 2.1 and 1.4). Optional global mode (Foldseek-TM) uses a 1.7× accelerated TM-align. Hits ranked by "structural bit score" = SW bit score × geometric mean of alignment TM-score and LDDT.
- **Speed.** On SCOPe40 (11,211 single-domain structures, all-vs-all): >4,000× faster than TM-align/Dali, >21,000× faster than CE. On AlphaFoldDB v1 (~365K structures), where Foldseek reaches full speed: ~184,600× faster than Dali, ~23,000× faster than TM-align. SARS-CoV-2 RdRp (PDB 6M71, 942 res) search of AlphaFoldDB took 6 s vs 33 h (TM-align) and 10 d (Dali); all top-10 hits were known RdRp homologs.
- **Sensitivity.** SCOPe40 superfamily AUROC: below Dali and TM-align, above CE, far above 3D-BLAST and CLE-SW. Foldseek-TM and Foldseek rank highest and third-highest on area under precision-recall; Foldseek-TM beats plain TM-align because its prefilter suppresses high-scoring FPs.
- **Multi-domain.** On a reference-free AlphaFoldDB multi-domain benchmark (100 queries, LDDT TP≥0.6/FP<0.25), Foldseek matches Dali, CE and TM-align. Inspecting 1,675/133,813 high-scoring "FPs" showed Foldseek (like 2D-aligner Dali) detects multi-domain homologs that differ only in relative domain orientation — cases TM-align overlooks because it requires global superposability.
- **E values** estimated via a neural net predicting Gumbel μ/λ from query composition and length, trained on 100K AlphaFoldDB structures; raw E values corrected by power 0.32.

## Methods (brief)
Structural alphabet learned via a modified VQ-VAE (PyTorch) trained on TM-align-derived residue pairs from SCOPe40 (4-fold cross-validation, no overfitting despite 492 parameters). A BLOSUM-like 3Di substitution matrix is derived from aligned-state substitution frequencies. Core implementation builds on the MMseqs2 framework with SIMD (SIMDe) acceleration; spatial-hashing grid for fast LDDT. Benchmarked against Dali, TM-align, CE, CLE-SW, 3D-BLAST, Geometricus and MMseqs2 on SCOPe40, AlphaFoldDB and HOMSTRAD.

## Limitations
SCOPe and HOMSTRAD benchmarks use almost exclusively single-domain proteins, so they cannot assess detection of locally shared domains between multi-domain proteins. The reference-free multi-domain benchmark requires arbitrary LDDT TP/FP thresholds. Only Cα traces are stored for database proteins (backbones reconstructed via PULCHRA for visualization), and webserver structure prediction is capped at 400-residue queries.

## Citations of interest
- Jumper et al. 2021 (AlphaFold) — source of the predicted-structure deluge motivating the tool.
- Lin et al. 2023 (ESMFold) — 617M metagenomic structures, the largest target database.
- Steinegger & Söding 2017 (MMseqs2) — the sequence-search framework Foldseek's prefilter and DB format build on.
- Zhang & Skolnick 2005 (TM-align) — primary structural-aligner baseline and the accelerated global-alignment backend.
- van den Oord et al. 2017 (VQ-VAE) — the discrete representation-learning method adapted to learn the 3Di alphabet.
- Mariani et al. 2013 (lDDT) — superposition-free score used for ranking and benchmark TP/FP labeling.
