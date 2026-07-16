<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: bio-multiomics
domains: [bio-multiomics]
title: Simultaneous CRISPR screening and spatial transcriptomics reveal intracellular, intercellular, and functional transcriptional circuits
authors: [Binan et al.]
year: 2025
doi: 10.1016/j.cell.2025.02.012
source_url: https://www.cell.com/cell/fulltext/S0092-8674(25)00197-7
drive_file_id: TODO
text_source: web
ingested_by: agent
---
# Simultaneous CRISPR screening and spatial transcriptomics reveal intracellular, intercellular, and functional transcriptional circuits

**Authors:** Loïc Binan, Aiping Jiang, Serwah A. Danquah, Vera Valakh, Brooke Simonton, Jon Bezney, Robert T. Manguso, Kathleen B. Yates, Ralda Nehme, Brian Cleary, Samouil L. Farhi
**Year:** 2025
**Venue:** Cell (188(8):2141–2158.e18; DOI: 10.1016/j.cell.2025.02.012)

## Abstract
The authors introduce **Perturb-FISH**, which combines imaging-based spatial transcriptomics (MERFISH) with parallel optical detection of in-situ-amplified CRISPR guide RNAs, so that genetic perturbation, transcriptome, and spatial neighborhood are read out simultaneously in the same cell. Applied to the LPS response in cultured macrophages, it recovers intracellular perturbation effects consistent with Perturb-seq and additionally uncovers density-dependent and intercellular regulation of the innate immune response. In 3D tumor xenografts it maps tumor–immune interactions altered by genetic knockout, and paired with live-cell calcium imaging in hiPSC astrocytes it links autism-risk genes to functional phenotypes.

## Key contributions
- New method (Perturb-FISH): T7-driven in-situ amplification of guide RNAs read out alongside MERFISH transcriptomics, preserving spatial context.
- Validated against Perturb-seq: **79% correlation** of shared-significant effects; **92%** replicate correlation; ~**81.7%** effect-size correlation at 50 cells/target.
- Discovered **intercellular** and **density-dependent** circuits invisible to dissociated single-cell methods.
- Extended to 3D xenografts (tumor–immune interactions) and to a functional calcium-imaging readout in astrocytes.

## Methods
Perturb-FISH inserts a T7 promoter between the U6 promoter and guide sequence in a lentiviral vector; T7 polymerase makes local copies of the guide in fixed cells, which are detected by DNA probes using a Hamming-weight-4, distance-4 barcode, then matched to MERFISH transcript readout via image registration and single-cell segmentation. The **primary immune system** is **THP-1-derived macrophages** stimulated with **LPS**, screened with **74 guides against 35 genes** (median 150 cells/perturbation, 2,184 control cells). Additional systems: CRISPRi of 127 ASD-risk genes in hiPSC astrocytes with calcium-imaging readout (76,400 cells); NF-κB perturbations in A375 melanoma xenografts in humanized mice. Circuits are classified as **intracellular** (perturbation → own transcriptome), **intercellular** (perturbation → neighboring control cells), and **functional** (perturbation → live-cell phenotype).

## Key results
- **Density-dependent immune genes:** TNF, IL1A vary with local cell density; TNF raw counts vary up to **1.34-fold** with neighbor number.
- **Density-conditioned perturbation effects:** *NFKB1* KO upregulates TNF only at low density (logFC 0.47, q 0.014); *TRAF6* KO downregulates IL1A more strongly at low density (−0.44, q 0.14) than high (−0.06, q 0.7).
- **Intercellular:** 9 perturbations significantly affected neighboring control cells; e.g. *MYD88* KO raised TNF in adjacent cells (logFC 0.83, q 0.06).
- **Xenograft:** 2,022 cell-intrinsic effects (32 perturbations) and **276 intercellular tumor–immune effects**; tumor NF-κB perturbations shifted T-cell markers (TNFRSF9, CD8A, TIGIT).
- **Astrocytes:** 566 significant perturbation effects; calcium phenotypes ("large peak," "inactive," "step," etc.) linked to specific ASD genes.

## Why it matters for our work
Our Track A/B task predicts, for **CRISPRi knockdowns in macrophages**, whether a (perturbation gene, target gene) pair goes **up / down / none**. This paper is a **directly matched biological prior**: same cell type (THP-1-derived macrophages), same stimulus axis (LPS/innate-immune), same perturbation modality (CRISPR loss-of-function), read out as gene-level transcriptional effects. Concretely usable priors:
- **Directional edges** in the NF-κB / TLR module (MYD88, TRAF6, NFKB1, IRAK, TNF, IL1A) — e.g. MYD88/TRAF6 loss ↓ downstream inflammatory genes — can seed or sanity-check our reasoning about pert→target direction.
- **Density/context dependence** is a caution: effect direction and magnitude here are not fixed but modulated by cell density and paracrine signaling, so a pair labeled "none" in one context may be real in another — useful when reasoning about ambiguous or weak labels.
- **Intercellular effects** show a perturbed gene can move a target in *neighboring* cells; if our data pools bulk/pseudobulk knockdowns this is a source of indirect (non-cell-autonomous) pert→target edges worth flagging.
Potential augmentation: the macrophage screen's effect table is a candidate external evidence source for retrieval-augmented reasoning on macrophage regulatory edges.

## Limitations / open questions
- Small targeted gene panel (35 genes / 74 guides in the macrophage screen) — narrow coverage vs. genome-scale screens; many pairs unmeasured.
- Effects are context-dependent (density, neighborhood), so single-number labels may not transfer across experimental conditions.
- Correlation with Perturb-seq is strong but imperfect (79%); modality-specific artifacts remain.
- KO/CRISPRi perturbation strength and efficiency vary per guide; magnitudes are assay-specific and may not equal our dataset's knockdown depth.
