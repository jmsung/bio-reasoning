# Roadmap

The team's single living plan for the BioReasoning Challenge 2026. Priority
ordered, top to bottom. Each item is a checkbox — checked when the work has
landed on `main`.

Workflow: see [`development.md`](development.md) — brainstorm → roadmap → branch → PR → merge.

## Convention

When a PR lands work that completes a roadmap item, `/pr-open` ticks the
box and prefixes the PR number — e.g. `- [x] (#3) EDA on training data`.
No manual edit needed; the roadmap stays in sync with merged work
mechanically.

If the scope of an item changes during implementation, edit the item in the
same PR. If a new item is needed, add it (priority-ordered) in the PR that
discovers it.

## Todo

Ordered by priority — understand → plan → build.

1. [x] (#4) **EDA on training data** — Perturb-seq distributions, class
   balance, missingness, train/test overlap, and GO / functional
   predictive-signal analysis.
2. [ ] **Audit augmentation candidates** — PerturbQA, Tahoe-100M (and other
   external Perturb-seq sources) as potential training augmentation.
   (split out of the original EDA item)
   - [x] test housekeeping-perturbation cell-type-invariance on Track A data
     (transferability hypothesis — see [[housekeeping-transfer-hypothesis]]) —
     **done via PerturbQA Stage-0 probe: transfer is selection-inflated on the
     overlap and gives no robust OOD lift; lane closed**
   - enumerate Tahoe's 50-line panel; flag myeloid/monocytic lines (THP-1,
     U937, …) closest to macrophages
   - **Perturb-seq lane go/no-go** → [`perturb-seq-lane-decision.md`](perturb-seq-lane-decision.md):
     **DECIDED — NO-GO, lane closed.** `research/perturb-seq-transfer-probe` measured no
     robust OOD lift (+0.0075 mean = one-seed noise; overlap DE 0.72 collapses to ~0.53 on
     OOD; CFA 1/3). External marginal DE is no better than the internal STRING-degree proxy;
     the ~0.65 direction ceiling stands. Higher-EV rank-1 bet = model-based DE crack.
3. [ ] **Port Track-A EDA scripts into the repo** — move the GO-annotation /
   enrichment / interaction scripts into `scripts/`, repoint to `data/raw/`,
   add the `mygene` dep, resolve the GO-cache (>500 KB) location. (follow-up
   from #4)
4. [ ] **Survey Kaggle approaches** — prior Perturb-seq / cellular response
   winners + the current competition's public notebooks, Discussions, and
   shared writeups from other teams.
5. [ ] **Literature survey + `/wiki-ingest`** — agent harness, meta-learning,
   gene perturbation, scRNA-seq prediction (ongoing; runs in parallel with 1–4).
   - PBio-Agent (LINCSQA) ingested; adaptation to our Track A/B worked out in
     [[pbio-agent-for-tracks]] — KG-reasoning agents + `none`-abstain judge.
     Prototype candidate for Track B.
6. [ ] **Foundation model survey for Track C** — open <10B candidates (Qwen,
   Llama, Gemma, …). Tracks A/B are locked to GPT-OSS-120B.
7. [ ] **Draft track-specific approach plans + per-member action plan** —
   A: prompt engineering, B: agent + tool design, C: FT recipe; architecture
   decisions; who owns what.
8. [ ] **Wire up GPT-OSS-120B inference** (Together AI / Fireworks API per
   organizer reply).
9. [ ] **Build A/B shared data pipeline** (`data/raw/<track>/` → train/test
   loaders).
10. [x] **First Track A submission baseline** (majority-class + a naive prompt). Track A evidence prior on the LB (0.529, PR #9); `track_a_prompt_only.py` schema-verified.
11. [ ] **Fix local pre-commit bootstrap** — Microsoft Store Python breaks
    `virtualenv` seeding; switch to a non-Store Python (`uv python install`)
    so `/dev-setup` + pre-commit hooks run. (dev-env; discovered in #4)
12. [x] (#22) **Track A two-stage GO-term model** — learned P(DE)·P(up|DE) heads over
    GO:BP term features for the perturbation *and* the target gene (the axis the
    evidence prior ignores). Beats the prior on the leak-free dual-OOD CV
    (~0.56 vs 0.534). Char-ngram/string-stat features were at chance — symbols
    are arbitrary; GO terms transfer across unseen perts/genes. Submission:
    `scripts/track_a_two_stage_submission.py`. **LB 0.561** (2026-07-16) vs prior
    0.529 — +0.032, OOD-val↔LB gap ~0.00. New Track A best.
13. [x] (#22) **Track B two-stage direction blend** — rank-blend the two-stage model's
    direction into the floor-to-prior submission (DE magnitude kept). Lifts
    OOD-val 0.5647 → 0.5712, beating the champion for every blend weight in
    (0,1). Submission: `scripts/track_b_blend_two_stage_submission.py`; eval:
    `scripts/track_b_two_stage_ood_val.py`. **LB 0.578** (2026-07-16, w=0.7) vs
    floor-to-prior 0.568 — +0.010, LB > OOD-val. New Track B best.
14. [x] **Track A neighbour-direction fusion** — fuse the SUMMER-style
    neighbour-retrieval direction (STRING-neighbour label borrowing, leak-free) into
    the two-stage GO submission via `fuse()`; DE kept, direction blended.
    `scripts/track_a_de_dir_submission.py` (feat/de-retrieval finding: DE-AUROC ~chance
    but DIR 0.651 vs 0.58). **LB 0.585** (2026-07-16) vs two-stage 0.561 — +0.024, and
    beats the prior overall best 0.578; OOD-val predicted +0.027. **New Track A + overall best.**
    (feat/de-dir-weight-tuning: swept the direction blend weight — broad OOD-val plateau at
    w~0.7-0.8 (mean 0.588) vs 0.584 equal-weight; submission default now `DIR_WEIGHT=0.75`,
    +0.004 OOD-val, not resubmitted so LB 0.585 stands. Sweep: `scripts/de_dir_weight_sweep.py`.)
15. [x] **Track B neighbour-direction fusion (parity with Track A)** — apply the same
    neighbour-direction lever to the Track B floored submission via the now track-agnostic
    `fuse_neighbour_direction`. **OOD-val 0.5916** (dir 0.570→0.624, 98% cov) vs the floored
    base 0.5647 (+0.028) and the prior Track B best dir-blend 0.5712 / LB 0.578 (+0.020).
    `scripts/track_b_de_dir_submission.py` (builder) + `track_b_de_dir_ood_val.py` (eval).
    **Kaggle LB 0.597** (2026-07-17) vs 0.578 — **+0.019, new Track B best**; OOD-val 0.5916
    predicted it (LB came in +0.005 higher, split held again).

## Completed

- [x] 2026-06-06 — `docs/scope-tracks`: scope tracks A/B/C and choose entry (PR #1).
- [x] Create shared Google Drive for papers/materials (7 subfolders seeded).
- [x] Create shared GitHub repo and invite Bing Hu + Joo Lee as collaborators.
