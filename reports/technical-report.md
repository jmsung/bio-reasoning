# Predicting Perturbation Response Under Dual-OOD Generalization: A Direction-First Approach to the BioReasoning Challenge 2026

**TL;DR — On a task designed so that both perturbations and target genes are unseen at test time, differential-expression detection is intrinsically near-chance, but *direction* (up vs. down) transfers. An honest dual-OOD validation split that predicts the leaderboard to within ~0.004 let us climb to Track A LB 0.586 and Track B LB 0.597, entirely by improving the direction axis.**

*Last updated: 2026-07-17 · Status: **draft** (good-shape internal report for later polish, not camera-ready).*

*Team: Jongmin Sung, Bing Hu, Joo Lee. BioReasoning Challenge 2026, MLGenX Workshop @ ICLR 2026 (Genentech BRAID).*

---

## Abstract

The BioReasoning Challenge 2026 asks whether LLMs and agentic systems can serve as *computational engines* for cellular biology: given a genetic perturbation and a target gene in mouse macrophages (CRISPRi), predict whether the target's expression goes `up`, `down`, or `none`. The scored metric is `mean(AUROC_de, AUROC_dir)` — one axis for "does this pair respond at all" (DE) and one for "which direction" (DIR). The test split is **dual-OOD**: test perturbations *and* test target genes are both disjoint from training (0/96 perts, 0/636 genes overlap), so memorization is worthless and only transferable biological reasoning generalizes.

Our central finding is a clean decomposition of the difficulty. Across six independent channel families — curated regulatory edges (CollecTRI, STRING 1-/2-hop), neighbour-label retrieval, char/prefix family retrieval, and a learned GO-term model — **the DE axis stays at chance (AUROC_de ≈ 0.50)**, while the **DIR axis is learnable and improvable** (AUROC_dir climbs from ~0.53 to ~0.65). Every gain we booked is a direction gain.

Two engineering disciplines made this legible. First, an **honest dual-OOD validation split** that reproduces the leaderboard to within ~0.004–0.005 (versus a naive 60-row CV that inflated Track B by 0.187 and inverted a conclusion). Second, a **two-stage DE×DIR decomposition** aligned to the metric's two AUROCs, into which orthogonal direction channels are rank-fused through a gated harness.

Headline results (Kaggle public LB): **Track A 0.586** (evidence prior 0.529 → two-stage GO 0.561 → neighbour-direction fusion 0.586) and **Track B 0.597** (agent 0.488 → floor-to-prior 0.568 → direction blend 0.578 → neighbour-direction fusion 0.597). We remain below the public field's headline tops (A ≈ 0.693, B ≈ 0.752), which are themselves unverified tutorial numbers; closing that gap, if reachable at all, requires bounding the direction ceiling. The external Perturb-seq data lane is now **closed end-to-end** — every cross-dataset borrow we tried moved the real LB by noise or worse (PerturbQA Δ+0.001, native-mouse Traxler Δ−0.005, LINCS ruled out before submission).

---

## 1. Background

### 1.1 The task

Participants predict how a **genetic perturbation reshapes a target gene's transcription** in mouse macrophages. Each row is a `(perturbation, target-gene)` pair — the perturbation gene is knocked down by CRISPRi, and the target gene is labelled `up`, `down`, or `none`. Training data is 7,705 rows (386 perturbations × 1,570 target genes); the test set is 1,813 rows (96 perts × 636 genes) [`docs/challenge.md`; `track-a-eda.md`].

Class balance (train): `none` 55.3%, `up` 30.6%, `down` 14.1%. `down` is the rare, hardest class [`docs/challenge.md`].

### 1.2 The metric — two AUROCs, not accuracy

The scored quantity is **`mean(AUROC_de, AUROC_dir)`**, confirmed from the vendored official scorer (`src/bio_reasoning/eval/kaggle_metric_track_a.py`) [`docs/kaggle-rules.md`]:

- **`AUROC_de`** ranks none-vs-DE by `prediction_up + prediction_down`.
- **`AUROC_dir`** ranks up-vs-down by `prediction_up / (prediction_up + prediction_down)` over DE-positive rows only.

Two consequences shape everything downstream. Predictions must be **graded floats**, not hard labels — a hard `up`/`down`/`none` throws away the ranking signal the metric consumes. And a constant "predict none" scores **≈ 0.5**, not 0.553; the majority-class 0.553 figure is an *accuracy* reference that does **not** apply here.

### 1.3 Why it is hard — dual-OOD by design

| Dimension | Train unique | Test unique | Overlap |
|---|---|---|---|
| Perturbations | 386 | 96 | **0** |
| Target genes | 1,570 | 636 | **0** |

Every test pair couples an **unseen perturbation with an unseen target gene** (overlap holds after case/whitespace normalization). A model cannot look up "what did this gene do before" — it must generalize from biological knowledge. This is the strongest structural argument for a reasoning-based approach over table lookup [`track-a-eda.md` §2]. It is also a trap for validation: any CV scheme that keeps perturbations or genes shared across folds is measuring memorization, not generalization (§3.1).

### 1.4 The LLM-as-computational-engine framing

The challenge tests whether LLMs can do more than *talk* about biology — whether they can serve as useful computational engines for predicting cellular behaviour [`docs/challenge.md`]. It fixes three axes of the LLM-engineering design space so contributions are comparable:

- **Track A — prompt-only.** Fixed base (GPT-OSS-120B), single forward call, no tools, ≤ 4,096 prompt tokens, 3 samples/row.
- **Track B — (multi-)agentic tool-use.** Same fixed base, ≤ 100 tools, ≤ 250 calls/row, ≤ 16,384 prompt tokens, tool-call traces required.
- **Track C — fine-tuning.** Any open model < 10B params, no tools. (Not entered by us.)

Tracks A, B, and C share the same `train.csv`/`test.csv` byte-for-byte and the same dual-OOD split — only the modelling constraints differ [`docs/challenge.md`]. Our posture: Track B (agentic) is the project's purpose, Track A is the unavoidable control the agent must beat to justify its cost.

---

## 2. Problem analysis

### 2.1 The metric decomposes into a hard axis and a learnable axis

Because the score is the mean of two AUROCs, the right question is not "how do we raise the aggregate" but "which sub-axis carries signal." EDA answered this before any modelling [`track-a-eda.md`]:

- **DE (does this pair respond at all) is deliberately hard.** The `none` negatives are count-matched per gene, so gene identity alone cannot separate DE from none. Per-perturbation DE-rate is flat (mean 0.454, std 0.058 — fixed by sampling design), and pairwise functional association (shared GO:BP terms between pert and target) predicts DE only weakly (AUROC 0.524 ≈ chance) [`track-a-eda.md` §3].
- **DIR (up vs. down, given DE) has real biological structure.** Direction is driven by perturbation *category*: knocking down a **housekeeping** gene skews targets **up** (~68–75%); knocking down an **immune** gene skews targets **down** (~58–66%) [`track-a-eda.md` §4].

### 2.2 The central structural insight

> For an unseen `(pert, gene)` pair, **DE-vs-none is near-chance while direction is learnable.**

This is the single most consequential fact in the project. It says: do not chase the aggregate; split effort across the two sub-metrics, and expect the returns to come from direction. Every subsequent result confirms it — the DE axis resisted six independent channel families, and every leaderboard gain we booked was a direction gain (§4, §5).

### 2.3 Class balance and its rank-metric trap

The 55.3% `none` majority tempts an "abstain when unsure" policy that is correct for an accuracy metric and *destructive* for a rank metric. Emitting `prediction_up = prediction_down = 0` produces a **tie at zero**, which carries no rank information. A large block of such ties drags AUROC toward 0.5 (§3.2, §5c) — the exact failure that sank our first agentic Track B submission.

---

## 3. Methods

### 3.1 An honest dual-OOD validation split (the keystone)

The prerequisite for trusting any offline number is a validation split that mirrors the test set's dual-OOD structure. We built two:

- **`doubly_disjoint_folds`** (`src/bio_reasoning/eval/split.py`) — hashes perturbations and genes independently into *k* buckets; a fold's eval rows share zero perts **and** zero genes with train (single-axis rows dropped) [`track-strategy.md`].
- **`holdout_split(df, seed, pert_frac=.4, gene_frac=.4)`** — a single stable dual-OOD partition (val = perts in the bottom `pert_frac` **and** genes in the bottom `gene_frac`; ~1,276 val rows / ~2,646 train). This is the fitness gate the trial loop optimizes against. The canonical scorer is `evaluate(labels, up, down) → {auroc_de, auroc_dir, mean}` [`track-strategy.md`; progress-report].

**Why naive CV inflates — and why it matters.** A *fixed functional* predictor (e.g. the evidence prior) scores identically under naive random-row CV and dual-OOD CV: it never sees fold labels, so it cannot leak. A *fold-fitted* predictor inflates. A per-perturbation label-frequency memorizing baseline scores **0.552 under naive random-row CV** and **collapses to 0.500 under dual-OOD** [`track-strategy.md`; progress-report]. This is the mechanism behind Track B's **0.675 CV → 0.488 LB** — a 0.187 inflation gap that *inverted the conclusion* ("beats floor" → "below floor"). The durable rule: the honest fitness surface for anything trained, tuned, or fold-fitted is the dual-OOD split, never naive/small CV.

The payoff: across every submission since, the split has predicted the leaderboard to within **~0.004–0.005** (§4). It is now the trusted offline gate — we rank ideas on it before spending Kaggle quota.

### 3.2 The evidence prior baseline

A no-LLM direction prior maps a perturbation's GO functional category to an up/down tendency (mygene.info annotations). It scores **LB 0.529 / local CV 0.534 / OOD-val 0.533** — a ~0 optimism gap, confirming it is CV-honest [`track-strategy.md`]. Its decomposition foreshadows everything: **AUROC_dir ≈ 0.557 (learnable), AUROC_de ≈ 0.500 (flat)**. This 0.529 is the floor any LLM or agentic approach must beat to justify its cost.

### 3.3 The two-stage DE×DIR decomposition

Borrowed from the public field's one genuinely transferable idea [`competitor-landscape.md`], the two-stage model learns `P(DE)` and `P(up | DE)` as **separate heads**, then recombines to the metric's two AUROCs: `up = P(DE)·P(up|DE)`, `down = P(DE)·(1 − P(up|DE))`. Crucially, our heads operate over **GO:BP term features for both the perturbation *and* the target gene** — the target-gene axis the evidence prior ignores — plus a shared-term count.

The featurization choice is load-bearing. **Char-ngram / gene-name string features score at chance** on the dual-OOD split (two-stage char-ngram 0.531 vs. prior 0.534), because symbols are arbitrary identifiers a string model cannot transfer across unseen ones. **GO:BP term vocabularies transfer** where raw symbols cannot (`track_a_two_stage_submission.py`) [`track-strategy.md`].

### 3.4 The fuse()/CFA rank-fusion harness

To add channels without regressing, we built a channel-agnostic validation harness — `bio_reasoning.models.fuse` — with two pieces [`curated-edges-fail-de-axis.md`]:

- **`fuse()`** — rank (not value) fusion, since the metric is AUROC; recombines into the metric's exact `up = s_de·r` / `down = s_de·(1 − r)` so `evaluate()` consumes it directly.
- **`cfa_gate()`** — admits a channel only if it is individually predictive (standalone DE-AUROC ≥ min, default 0.55) **and** diverse (low |Spearman| vs. the current `s_de`).

The gate earns its keep by rejecting cheaply, *before* the expensive build: a 2-hop STRING proximity probe scored DE-AUROC 0.543 (< 0.55 bar), and we killed the ~121 MB RWR build on that evidence with no LB submission spent.

### 3.5 The neighbour-retrieval (SUMMER-style) direction channel

For an unseen `(pert, gene)`, we borrow the *measured labels* of TRAIN rows whose pert or gene is a **STRING neighbour** (leak-free: val pert/gene held out, own pair excluded; ~98–100% coverage) [`neighbor-retrieval-direction-lever.md`]. Its behaviour is the project thesis in miniature: **DE-AUROC 0.498 ± 0.006 (dead chance)** but **DIR-AUROC 0.651 ± 0.047** (seeds 0–4, all ≥ 0.58). Fusing its direction `r` into the two-stage GO model lifts OOD-val mean **+0.027 ± 0.009**, entirely on `AUROC_dir`.

The lever lives in the **retrieval key**, not the borrowing mechanism. A char/prefix gene-family key (neighbours sharing e.g. `Rpl*`, `Ifit*`) failed *both* axes (DE 0.502, DIR 0.519) — naming convention does not track co-regulated direction on real OOD symbols. Labeled-pair graph neighbours (STRING/GO) place co-regulated genes together, so their up/down tendency transfers [`neighbor-retrieval-direction-lever.md`].

### 3.6 Floor-to-prior for Track B (never emit 0/0)

The Track B fix for the abstention collapse: post-process every `(0,0)` tie to the perturbation's graded category prior — extend the parse-fail fallback to *all* would-be abstentions, guaranteeing every row carries ≥ the 0.529 prior signal. This is a pure post-processing step on saved predictions (no re-inference, ~$0). It is the base onto which learned direction is later fused (§4).

---

## 4. Results

### 4.1 The ladder

All scores are Kaggle **public** LB unless marked OOD-val. Every submission traces to a source in the progress report or a wiki finding.

| # | Track | Approach | LB | OOD-val | LB↔val gap | Note |
|---|---|---|---|---|---|---|
| — | ref | Constant "predict none" | ≈ 0.500 | 0.500 | — | metric is AUROC, not accuracy |
| 1 | A | Evidence prior (GO direction, no LLM) | **0.529** | 0.533 | ~0.00 | the real floor; DIR carries it, DE flat |
| 2 | A | Two-stage GO-term (`P(DE)·P(up\|DE)`) | **0.561** | ~0.56 | ~0.00 | +0.032 over prior; string features at chance |
| 3 | A | Neighbour-direction fusion (STRING-neighbour DIR into #2) | **0.586** | +0.027 predicted | ~0.003 | **Track A best**; DE ~chance, gain all DIR |
| 4 | B | Agent harness v1 (multi-agent, gpt-oss-120b) | **0.488** | (60-row CV 0.675) | 0.187 | **below floor** — 72% `0/0` ties collapsed rank |
| 5 | B | Floor-to-prior (every `0/0` → graded prior) | **0.568** | 0.564 | 0.004 | first Track B above floor; +0.039 |
| 6 | B | Direction blend (two-stage DIR into #5, w=0.7) | **0.578** | 0.571 | +0.007 (LB > val) | orthogonal learned DIR still lifts |
| 7 | B | Neighbour-direction fusion (STRING-neighbour DIR into floored base) | **0.597** | 0.5916 | ~0.005 | **Track B best** (2026-07-17); dir 0.570 → 0.624 |
| — | field | Public LB top (unverified tutorials) | A ≈ 0.693 / B ≈ 0.752 | — | — | we remain below the front |

Sources: rows 1–3 [`track-strategy.md`; roadmap #12/#14; progress-report]; row 4 [`track-b-abstention-failure.md`]; rows 5–6 [`track-b-abstention-failure.md`; progress-report]; row 7 [`track-strategy.md` `feat/track-b-neighbour-dir-parity`; predicted OOD-val 0.5916, LB 0.597 on 2026-07-17].

### 4.2 The per-axis story

Every gain in the table above is a **direction** gain; the DE axis never moves off chance.

- **Track A prior → two-stage GO (+0.032):** DE stays ~0.500, DIR improves via GO-term features over the target gene [`track-strategy.md`].
- **Track A two-stage → neighbour fusion (+0.024):** DE-AUROC ~chance across 4 channel families; the retrieval signal lives entirely in DIR (0.651 standalone) [`neighbor-retrieval-direction-lever.md`; progress-report].
- **Track B floored → neighbour fusion (+0.029 offline):** `AUROC_de` unchanged (0.560, Spearman 0.98 vs. floored base), `AUROC_dir` 0.570 → 0.624 [`track-strategy.md`].

The neighbour-direction lever is **base-agnostic** — the same code path lifted Track A's *model* base (LB 0.586) and Track B's *floored* base (OOD-val 0.5916 → LB 0.597). Direction is the live axis on every base; DE stays dead.

### 4.3 The dual-OOD ↔ LB gap has held throughout

Across the whole ladder, the honest split predicted the leaderboard tightly: Track A two-stage (gap ~0.00), Track A neighbour-fusion (predicted +0.027, delivered +0.024, gap ~0.003), Track B floor-to-prior (gap 0.004), Track B neighbour-fusion (predicted 0.5916, LB 0.597, gap ~0.005). The 0.187 inflation that sank the raw agent is fully gone once the split mirrors the test structure. This is the difference between a trustworthy offline gate and a mirage.

---

## 5. Key findings / discussion

**(a) The entire A/B gap is the DE axis — and DE looks intrinsically hard for unseen pairs.** Six independent DE channels all landed at chance on the dual-OOD split: CollecTRI signed TF-regulon (0.4% coverage), STRING 1-hop edges (1.6% coverage), STRING 2-hop proximity (0.543), STRING-neighbour label retrieval (0.498), char/prefix family retrieval (0.502), and the learned GO model (0.500) [`curated-edges-fail-de-axis.md`; `neighbor-retrieval-direction-lever.md`; `rank1-plan.md`]. The structural reason for the curated channels: the task scores *arbitrary* pairs, but curated databases only assert a ~1–2% high-confidence slice — "is this a known edge?" is almost always "no" regardless of true DE. Three later DE angles closed the axis for good, each along a different attack: (i) **external cross-dataset borrowing** — a native-mouse Traxler transfer moved the real LB by **Δ−0.005** and PerturbQA by **Δ+0.001** (noise), so no held-out perturbation atlas rescues DE; (ii) **structural coverage** — 82 of 96 test perturbations are essential genes never screened in any borrowable dataset, so a lookup path cannot exist for most test rows; (iii) **model-based reasoning** — gpt-oss chain-of-thought DE calls scored ≈ chance (synthpert 18/51). DE for a truly-unseen `(pert, gene)` pair appears near-unpredictable from any pair-external feature, learned model, or external table. An error-analysis dissection of the **incumbent itself** (two-stage GO + neighbour-fused direction; reproduced at pooled dual-OOD mean 0.584 / DE 0.510 / DIR 0.658) closes the last escape hatch: its DE-AUROC sits at chance in **every** perturbation category (housekeeping 0.495, other 0.520, immune 0.537), so the DE failure is *uniform*, not a weak average concealing a learnable sub-population — subset or category-gating tricks cannot recover it [`track-a-error-structure.md`]. **The capstone is a leakage-allowed oracle upper-bound.** To rule out "our features are just weak," we fit a DE head *permitted to cheat* — given gene identity, per-gene/per-perturbation leave-one-out DE-rate, and full-data marginals — and scored it on the same dual-OOD split (`de_ceiling_probe.py`, `de-unlearnable-on-dual-ood.md`). In-sample it reads 0.960, but that number is a **split-artifact**: on a doubly-disjoint split the LOO DE-rate leaks each validation label into its gene-mates, which is unachievable at test where identities are unseen. Deriving the rates from *train only* — the honest construction — collapses every rate channel to the prior by definition and the oracle lands at **AUROC_de 0.555 ± 0.036 ≈ chance** (the lone non-chance residue, gene_count 0.585, is a label-free row-count artifact, not a DE mechanism). An honest DE model can only do worse than this oracle, so the result is a hard upper bound: **DE is unlearnable-by-design on this split — not merely un-cracked by the channels we tried, but un-rankable even by a cheating oracle.**

**(b) DIRECTION is the live lever — every gain is direction.** DIR transfers because related TFs/genes push targets in correlated directions, so a neighbour's up/down tendency is predictive even when the pair itself is unseen. Every leaderboard improvement — GO-term target features, neighbour-retrieval `r`, cross-track fusion — moved DIR, never DE [`neighbor-retrieval-direction-lever.md`].

**(c) The honest split is predictive → a trustworthy offline gate.** With the LB↔val gap pinned at ~0.004–0.005, we iterate on the dual-OOD surface without paying a Kaggle submission per step. Concretely, this let us kill the STRING RWR build (§3.4), reject the α-blend lever, and confirm neighbour-DIR fusion offline before any upload. The contrast with the 60-row CV (gap 0.187, which *inverted* a conclusion) is the whole argument for validation discipline in a rank metric on OOD data.

**(d) The char-ngram field claim does not reproduce on a true dual-OOD split.** The public field's headline story is gene-name character n-grams + classical ML reaching ~0.693 [`competitor-landscape.md`]. A *proper* TF-IDF char-ngram probe, submitted to the board, scores only **0.552 on the real Kaggle LB** — a genuine leaderboard number, but below our two-stage GO model (0.561, row 2) and far short of the claimed 0.693 [`rank1-plan.md`]. Either the field's test is easier than a true dual-OOD split, or the headline numbers (printed in none of the six vote-leading notebooks) are unverified. We could not extract the claimed name-structure signal into a score that beats functional GO features on genuinely disjoint symbols.

**(e) Featurization beats architecture — foundation models lose to linear on unseen perturbations.** Three 2025 benchmarks (Ahlmann-Eltze *Nat. Methods*; scPerturBench; Palla TabPFN) show scGPT/GEARS/State/scFoundation losing to a linear baseline in the unseen-perturbation regime — exactly ours [`rank1-plan.md`]. The implication we adopted: never run foundation models end-to-end; use them only as an embedding/feature source. GO-term features beat string features not because of a better model but because they encode transferable functional structure.

---

## 6. Limitations & threats to validity

- **Cross-seed noise floor.** The dual-OOD `holdout_split` carries **σ ≈ 0.05–0.06** across seeds. Single-split lifts held on the LB for every submission so far, but exact deltas are soft; multi-seed pooled confirmation is cheap insurance before trusting a single-split difference [`track-strategy.md`; `rank1-plan.md`].
- **The field's headline numbers are unverified.** The public A ≈ 0.693 / B ≈ 0.752 come from vote-leading *tutorial* notebooks with **no printed CV or LB scores**; none call an LLM, and char-string ML cannot plausibly reach 0.752 [`competitor-landscape.md`]. Treat the gap to the "front" as uncertain — it may be closer than the headline, or the leaders may win on external knowledge we have not tapped.
- **We remain below the field.** Even taking the tops at face value, our best (A 0.586 / B 0.597) sits ~0.10–0.16 below them on a 0.5-baseline metric. Real headroom remains; direction alone may not reach it.
- **Single-split caveats.** Most channel comparisons use one `holdout_split` seed for speed. The DE kill-count and the DIR lift are multi-seed confirmed, but finer weight-tuning decisions were made on flat, within-noise plateaus (e.g. the neighbour-vs-model blend weight) and should not be over-read.
- **Track B tool-legality is unconfirmed on the JS-rendered rules tab.** Our reasoning that an offline model (TabPFN) is a legal tool is inference from the "fixed LLM, no fine-tuning" clause, not a confirmed reading [`kaggle-rules.md`; `tabpfn-for-perturbation-tracks.md`].

---

## 7. Conclusion & next directions

The project reduced a two-axis prediction problem to a single actionable statement: **DE is dead, direction is the game.** An honest dual-OOD split turned that statement into a trustworthy gate, and a two-stage decomposition plus a gated rank-fusion harness turned direction gains into leaderboard climbs — Track A to 0.586 and Track B to 0.597, every step a direction step.

Two of the original rank-1 levers are now **closed**, which sharpens what remains [`rank1-plan.md`]:

1. **Maximize direction (live).** Fuse the direction channels (GO-DIR + neighbour-DIR + gene-embedding-DIR) through the CFA gate — with ≥ 2 gate-passing channels, the fuse harness and a meta-loop bandit over channels are justified.
2. **Reframe gene embeddings as a direction lever (live)** (GPT/LLM gene embeddings > GO terms for unseen genes, per GenePert/Scouter), feeding the DIR head, not a DE hope.
3. **Bound the DIR ceiling.** We are at ~0.65 DIR; fusion + embeddings may add a little, but the field's 0.693 does **not** reproduce on a true dual-OOD split (§5d), so ~0.70 is not a credible target. With DE pinned near 0.55, the honest ceiling looks like ~0.60–0.65 — measure it before over-investing.
4. **DE is done — closed by a ceiling, not deferred.** Every remaining DE angle has now been fired and missed (§5a): the marginal-property shot, native-mouse cross-dataset transfer (real-LB **Δ−0.005**), a structural audit (82/96 test perts are essential genes never screened in any borrowable dataset), and gpt-oss chain-of-thought DE calls (≈ chance, synthpert 18/51). An error-analysis dissection of the incumbent adds the category constraint: DE-AUROC is at chance across *every* perturbation category (not a concealed sub-population), with neighbour coverage already at 98.9% [`track-a-error-structure.md`]. The **terminal** proof is the leakage-allowed oracle ceiling (§5a): even a head permitted to cheat caps at **AUROC_de 0.555 ± 0.036 ≈ chance** on the honest dual-OOD split [`de-unlearnable-on-dual-ood.md`]. The negative result is not "we didn't find a channel" but "no channel exists" — no further DE shots are planned.
5. **External-data lane closed end-to-end — not deferred.** The Perturb-seq augmentation lane (Replogle / PerturbQA, native-mouse Traxler, and the housekeeping-transfer hypothesis for cross-dataset borrowing) is dead: real-LB deltas were noise or negative (PerturbQA **Δ+0.001**, native-mouse **Δ−0.005**) and LINCS was ruled out before any submission. No path to rank up runs through external data.

**The live axis of work is the self-improving loop program**, not new modelling levers. The trial-loop environment and output-styles landed (#53–56); the two weakest variants (④ synthpert, ⑤ bakeoff) were retired; a scheduling deadlock was fixed (#57); and cheap-verify plus prompt-wording refinements are in progress. The binding constraint is **throughput — ~1.4–2.8 h per trial** — so heavy hyperparameter/optimization work is deferred until the loop runs faster. Making the loop cheap and fast is the prerequisite to spending it on the direction levers above.

With DE closed and external data dead, the strategic picture is settled to a single question: can the self-improving loop push direction to its ~0.60–0.65 honest ceiling cheaply enough to matter against an (unverified) 0.693/0.752 front? We drive direction through the loop, submit, and let the real leaderboard settle it.

---

## References

**Project wiki findings & methods (ground truth for this report):**

- `knowledge/wiki/findings/track-a-eda.md` — data structure and the DE-hard / DIR-learnable decomposition.
- `knowledge/wiki/findings/track-a-error-structure.md` — incumbent error-structure: DE uniformly at chance across categories; neighbour coverage maxed at 98.9%.
- `knowledge/wiki/findings/track-b-abstention-failure.md` — the rank-metric abstention collapse (0.675 CV → 0.488 LB) and the floor-to-prior fix.
- `knowledge/wiki/findings/competitor-landscape.md` — the public field is LLM-free string-ML; the two-stage decomposition as the transferable win.
- `knowledge/wiki/findings/neighbor-retrieval-direction-lever.md` — neighbour retrieval fails DE, is a robust +0.027 direction lever; the key decides DIR transfer.
- `knowledge/wiki/findings/curated-edges-fail-de-axis.md` — curated edges too sparse/weak for DE; the `fuse()`/CFA gate harness.
- `knowledge/wiki/findings/de-unlearnable-on-dual-ood.md` — the DE negative result: a leakage-allowed oracle caps AUROC_de at 0.555 ≈ chance; DE is unlearnable-by-design on the honest dual-OOD split.
- `knowledge/wiki/findings/tabpfn-for-perturbation-tracks.md` — tabular foundation models as a Track A baseline / Track B tool.
- `knowledge/wiki/findings/housekeeping-transfer-hypothesis.md` — housekeeping-perturbation cell-type-invariance for cross-dataset augmentation; the borrow was tested and **closed** (real-LB deltas noise-or-negative, §5a / §7).
- `knowledge/wiki/methods/pbio-agent-for-tracks.md` — adapting the PBio-Agent KG-reasoning framework; the `none`-abstain judge.
- `reports/progress-report.md` — the append-log of all measured results.
- Internal team strategy synthesis and the rank-1 attack plan (team-private working notes; the results they cite are reproduced above).

**External literature (cited via the wiki):**

- Palla et al., *Tabular Foundation Models Are Competitive Cellular Perturbation Predictors Across Biological Scales* (CZ Biohub, 2026; bioRxiv 10.64898/2026.06.28.735106) — TabPFN/TabICL SOTA for perturbation prediction.
- Ahlmann-Eltze et al., *Nat. Methods* (2025) — deep models lose to linear baselines on unseen perturbations; scPerturBench (2025) corroborates.
- GenePert / Scouter — ridge over GPT gene embeddings beats scGPT/GEARS and generalizes to unseen perturbations.
- Wu et al., *PerturbQA* / SUMMER — neighbour-retrieval no-fine-tune SOTA for DE/direction (the retrieval-done-right template).
- Kim et al., *PBio-Agent (LINCSQA)* (2026) — training-free multi-agent KG-reasoning for perturbation direction.
- Zhang et al., *Tahoe-100M* (2025) — large-scale chemical-perturbation atlas (augmentation candidate).

**Challenge & competition:**

- Challenge overview: https://genentech.github.io/BioReasoningChallenge/
- Reference implementation: https://github.com/genentech/bioreasoningchallenge
- Tracks A / B / C on Kaggle (`ml-gen-x-bioreasoning-challenge-track-{a,b,c}`).
- `docs/challenge.md`, `docs/kaggle-rules.md`, `docs/roadmap.md` — canonical team docs.
