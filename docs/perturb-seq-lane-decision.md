# Perturb-seq data lane — go/no-go decision

**Status: DECIDED — NO-GO (lane closed, real-LB confirmed).** The OOD-val gate measured no robust lift (`research/perturb-seq-transfer-probe` Goal 5), and the reserved real-LB read now agrees: +external = 0.586 vs baseline 0.585 (Δ+0.001, `research/perturb-seq-real-lb-overlap`). See [Decision](#decision) and [Real-LB confirmation](#real-lb-confirmation-2026-07-17-researchperturb-seq-real-lb-overlap).

**Question.** The DIRECTION lane is closed on the real leaderboard (Track A LB **0.586** at weighted best « field 0.693), and DE-vs-none is dead across 6 internal channels. Should the team open the **Perturb-seq data lane** — using external perturbation datasets (Replogle, PerturbQA, Dixit) as a new signal source — as the path to a materially better Track A score?

This doc is the decision *frame*: what the lane is, what it costs, what the evidence says it can buy, and the explicit criteria the go/no-go hinges on. It is deliberately **decision-only** — the data pull and transfer measurement live in `research/perturb-seq-transfer-probe`; this doc consumes that branch's numbers.

Grounded in the consult-KB gate (`.claude/CLAUDE.md`); cites are to `knowledge/` pages.

---

## 1. Candidate datasets

| Dataset | Scale | Organism | Modality | Maps to `{up,down,none}`? |
|---|---|---|---|---|
| **Replogle 2022** (genome-scale Perturb-seq) | ~2.5M cells; ~9,866 GW targets + K562/RPE1-essential subsets | **Human** (K562, RPE1) | CRISPRi knockdown expression | Needs pseudobulk + DE-threshold + mouse↔human ortholog map |
| **PerturbQA** (Wu 2025) | ~599k curated pairs, 4 CRISPRi lines | **Human** (K562, RPE1, HepG2, Jurkat) | **Curated `up/down/none` labels** | **Directly** — same task format, no pseudobulking |
| **Dixit 2016** (original Perturb-seq) | ~200k cells, <25 TF perts | **Mouse** BMDCs + LPS | CRISPR-KO expression | Best species/lineage match but too small for a corpus |

Cites: `knowledge/source/2022-replogle-genome-scale-perturb-seq.md`, `knowledge/source/2025-wu-perturbqa.md`, `knowledge/source/2016-dixit-perturb-seq.md`; compute/tooling in `knowledge/wiki/methods/perturb-seq-data-assessment.md`.

**Critical organism gap.** The challenge is **mouse BMDMs** (`knowledge/source/2026-bioreasoning-challenge-overview.md`); Replogle and PerturbQA are **human** → all transfer routes through a mouse↔human ortholog map. Only Dixit is native mouse, and it is too small to serve as a retrieval corpus. The cheap, high-coverage route is **PerturbQA's curated CSVs** (pandas only — no `pertpy`/`scanpy`/single-cell download); the expensive route is a genome-scale Replogle pseudobulk pull.

## 2. Does external transfer even work? (literature)

The published consensus is **strongly cautionary for the OOD-both-axes regime** — which is exactly our test split:

- **Ahlmann-Eltze 2025** (Nat. Methods): across 4 CRISPR datasets, **no DL/foundation model beat linear/mean baselines** on unseen perturbations. The one thing that consistently won: a linear model with perturbation embeddings pretrained on the *other* cell line — i.e. transfer works via **direction/response**, while generic atlas/FM augmentation washed out. `knowledge/domains/bio-multiomics/source/2025-ahlmann-eltze-dl-perturbation-vs-linear.md`.
- **Csendes 2025**: Train-Mean beat scGPT/scFoundation on all 4 Perturb-seq datasets; root cause = **low perturbation-specific variance**. `knowledge/source/2025-csendes-fm-perturb-benchmark.md`.
- **Hou 2026** (leakage-controlled scFM benchmark): across 13 scFMs, **none beat an additive baseline** for perturbation prediction. `knowledge/source/2026-hou-scfm-benchmark.md`.
- **Yuan 2026** (Plausibility ≠ Prediction): LLM predictors are near-chance per-gene and **over-call DE** (dangerous against a `none`-heavy label set); contrastive neighbor/KG retrieval lifts per-gene AUROC 0.50→~0.57–0.63, but **no zero-overlap regime was tested**. `knowledge/domains/ai-reasoning/source/2026-yuan-plausibility-not-prediction-llm-perturbation.md`.

**The one positive signal.** **Palla 2026** (Tabular FMs): TabPFN/TabICL rank #1 on every perturbation task including cross-cell-type — but absolute power is **modest** (0.22–0.58 cosine vs 0.97 oracle), and on genome-wide primary-cell knockouts **93% of logFC is within ±0.1** (near-null). `knowledge/domains/bio-multiomics/source/2026-palla-tabular-foundation-models-perturbation.md`.

**Ceiling read.** OOD transfer degrades sharply; the transferable slice is the **direction of a broad conserved program** (housekeeping-up / immune-down), not pair-specific DE. `knowledge/wiki/findings/direction-transfers-de-doesnt.md`; `knowledge/wiki/findings/housekeeping-transfer-hypothesis.md`.

## 3. Leakage risk — NOT a blocker

- The challenge **explicitly allows** PerturbQA and Tahoe-100M as augmentation (permissively licensed). `knowledge/source/2026-bioreasoning-challenge-overview.md`.
- PerturbQA is built from / includes Replogle K562/RPE1 — a flagged leakage-check requirement.
- **The check was run and PASSED:** Track A is mouse macrophage; PerturbQA is human K562/RPE1/HepG2/Jurkat → disjoint on **both** species and cell type, so Track A labels cannot derive from it and measured transfer is **not** source-inflated. (`research/perturb-seq-transfer-probe`).

## 4. Coverage — NOT a blocker

The probe's uppercase-ortholog map covers **64/96 (67%) of TEST perts** and 242 train-overlap pairs. The essential-gene core (where signal concentrates) is well-measured. (`research/perturb-seq-transfer-probe`).

## 5. Cost of opening the lane

- **Cheap route (already de-risked by the probe):** PerturbQA curated CSVs on pandas alone — no `pertpy`/`scanpy`, no single-cell download. Most of the measured signal came from here.
- **Expensive route (may be unnecessary):** genome-scale Replogle pseudobulk pull — tens–100+ GB server-side, ortholog mapping, DE-thresholding, new deps. `knowledge/wiki/methods/perturb-seq-data-assessment.md`.
- **Integration:** an external-retrieval channel reusing the existing `fuse()` / `cfa_gate()` harness (~500 lines per the pre-probe scoping).

## 6. What the probe has already measured (and what it hasn't)

`research/perturb-seq-transfer-probe` (Goals 1–3 done) **partly overturns** the pre-probe pessimism, then re-imposes it at the level that matters:

- **Stage-0 agreement gate CLEARED:** on 242 overlap pairs, external→Track-A **DE-AUROC 0.722, DIR-AUROC 0.951** (shuffle control 0.50 — signal is real).
- **But DE transfer is MARGINAL, not pair-specific:** per-PERT LOO 0.676, **per-GENE LOO 0.538 (chance)**. The signal is conserved *pert-level responsiveness* ("essential perts drive broad DE"), not the pair-specific DE that is the true bottleneck. It does beat our internal STRING-degree marginal proxy (0.536). The DIR 0.95 is real but **selection-inflated** (overlap = robustly-DE, unambiguous pairs).
- **STILL PENDING (probe Goals 4–6):** the **CFA orthogonality** of the external channel vs existing GO-DIR + neighbour-DIR, and the **actual OOD-val fusion lift** vs the 0.5663 baseline (bar: ≥ +0.005 across seeds). The probe's own framing: marginal pert-DE-propensity may be **redundant** with existing channels and get CFA-rejected. **The go/no-go is not answered until that number lands.**

## 7. The crux — what the decision hinges on

1. **Does the external channel *fuse* for a real OOD lift, or is it redundant?** Stage-0 measured *on-overlap agreement*, not *held-out lift*. The transferable DE is marginal (pert-level) — exactly the kind of signal existing channels may already capture. **Decisive number = probe Goal 5's fused-mean on `holdout_split` vs 0.5663.**
2. **Ceiling vs cost.** Even a successful lane reinforces **direction (already ~0.65-capped)** and adds only *marginal* pert-DE, not pair-specific DE. Honest mean-AUROC ceiling stays ~0.60–0.65 — ~0.10 below the field's **unverified** 0.693 (which does not reproduce on a true dual-OOD split; `knowledge/wiki/findings/competitor-landscape.md`). The cheap PerturbQA-CSV route means the *cost* of a first real submission is low, so the bar for "worth trying once" is correspondingly low.
3. **Is rank-1 reachable by *any* data lane?** Standing team conclusion: rank-1 likely needs the untried **model-based DE crack** (token-logprob self-consistency, endpoint-gated) *or* the field sitting on an easier-than-dual-OOD split — **not more direction/data**. The data lane's honest best case is "a modest, bounded lift on an axis we already lead," not rank-1. `knowledge/wiki/findings/direction-transfers-de-doesnt.md`.

## Decision

The flip was **auto-resolved by one number** — probe Goal 5's fused OOD-val mean-AUROC
on `holdout_split`. The rule below was written to decide itself the moment that number
landed; it has ([Resolution](#resolution--the-rule-fired-no-go) — **NO-GO**).

### Go/no-go criteria (decision rule)

Let `L` = the external-retrieval channel's fused OOD-val mean-AUROC (`holdout_split`,
averaged across seeds) vs the **0.5663** baseline, and let the **CFA gate** verdict be
ADMIT/REJECT for orthogonality vs the existing GO-DIR + neighbour-DIR channels
(`research/perturb-seq-transfer-probe` Goal 4–5).

- **GO (cheap)** — build the PerturbQA-CSV external-direction channel into the live
  submission and spend **one** Kaggle read — **iff** `L ≥ +0.005` across all/most seeds
  **AND** the CFA gate **ADMITs** the channel. (This is the probe's own pre-registered bar.)
- **NO-GO** — if `L < +0.005` (within seed noise) **OR** the CFA gate **REJECTs** the
  channel as redundant. Close the lane: the external signal is already captured by
  existing direction/marginal channels; do not build further.
- **Scope guard even on GO** — GO authorizes only the **cheap PerturbQA-CSV channel +
  one LB read**, *never* the genome-scale Replogle pipeline (tens–100+ GB, ortholog +
  pseudobulk + new deps). Replogle is justified **only** if the cheap channel shows a
  *real LB lift* **and** a mechanism for **pair-specific** (not just marginal pert-level)
  DE emerges — neither is on the table today.

### Recommendation (conditional, skeptical prior)

**Lean: complete probe Goal 5; take the one cheap submission only if it clears the bar;
otherwise close the data lane. Do not open the expensive Replogle pipeline on current
evidence.** The prior points to NO-GO / redundant:

1. The transferable DE is **marginal (pert-level), not pair-specific** (per-gene LOO
   0.538 = chance) — it may already be captured by our channels and get CFA-rejected.
2. It reinforces **direction, which is already ~0.65-capped**, and the external DIR 0.95
   is **selection-inflated**; the honest ceiling stays ~0.60–0.65.
3. The field's 0.693 target is **unverified** and does not reproduce on a true dual-OOD
   split, so "beat the field" may not be a real target from a data lane at all.

The counterweight is that the **cheap** route is genuinely cheap (PerturbQA CSVs, pandas)
and Stage-0 surprisingly cleared — so finishing the fusion test and taking one bounded
shot costs little. The expensive lane, by contrast, has **bounded EV against a ~0.65
ceiling** and should stay closed unless the cheap shot changes the picture.

**What would change this:** a fused OOD lift materially above +0.005 that the CFA gate
admits, *and* an LB read confirming it — or a mechanism that turns marginal pert-DE into
**pair-specific** DE (the true bottleneck). Absent those, the higher-EV rank-1 bet is the
**model-based DE crack** (token-logprob self-consistency; `feat/de-logprob-self-consistency`),
not this data lane.

### Resolution — the rule fired NO-GO

`research/perturb-seq-transfer-probe` Goal 5 reported (seeds 0/1/2, `holdout_split`):

| config | mean | Δ vs baseline 0.5819 |
|---|---|---|
| baseline `[GO, neighbour]` | 0.5819 | — |
| `+ external (DE+DIR)` | 0.5894 | **+0.0075** |

Applying the rule: the +0.0075 mean **fails the "≥ +0.005 across seeds" bar** — it is
**one-seed noise** (seed1 +0.022; seeds 0/2 +0.002 / −0.002), the overlap DE 0.72
**collapses to ~0.53 on OOD** (selection-inflated, as flagged), and the **CFA gate passes
only 1/3 seeds** (direction redundant with neighbour-DIR). Not `L ≥ +0.005 across seeds`,
not `CFA ADMIT` → **NO-GO.**

**Decision: NO-GO — the Perturb-seq data lane is closed.** The external channel is no
better than our internal STRING-degree marginal-DE proxy on OOD, and the expensive
Replogle pipeline is not opened. The honest ~0.65 direction ceiling stands; the
higher-EV rank-1 bet is the **model-based DE crack** (token-logprob self-consistency;
`feat/de-logprob-self-consistency`), not more data.

### Real-LB confirmation (2026-07-17, `research/perturb-seq-real-lb-overlap`)

The NO-GO above rested on the OOD-val gate; the doc's GO branch had reserved one real-LB
read that the gate pre-empted. That read is now spent — the same channel set the OOD-gate
scored, submitted to the **real Track A board** (generic `fuse`, 1813 test rows, PerturbQA
covering 65.9%):

| Submission | Public LB |
|---|---|
| baseline `fuse([GO, neighbour])` | **0.585** |
| `+ external fuse([GO, neighbour, PerturbQA DE+DIR])` | **0.586** |

**Δ = +0.001.** The real board **confirms** the OOD-val verdict — external adds nothing even
with 66% coverage. This closes the last escape hatch: the "we killed the lane on a too-hard
*synthetic* split" hypothesis is **refuted on the real board itself**. The dual-OOD split was
honest; rank-1's ~0.75 does **not** come from PerturbQA-retrieval DE. Lane stays **CLOSED**,
now confirmed end-to-end. Next: the model-based DE crack (`feat/de-logprob-self-consistency`).
