# Roadmap

The team's single living plan for the BioReasoning Challenge 2026. Priority
ordered, top to bottom. Each item is a checkbox — checked when the work has
landed on `main`.

Workflow: see [`development.md`](development.md) — brainstorm → roadmap → branch → PR → merge.

## Convention

When a PR lands work that completes a roadmap item, the **same PR** must
check the box here. The roadmap should never lag behind merged work.

If the scope of an item changes during implementation, edit the item in the
same PR. If a new item is needed, add it (priority-ordered) in the PR that
discovers it.

## Todo

Ordered by priority — understand → plan → build.

1. [ ] **EDA on training data** — Perturb-seq distributions, class balance,
   missingness; audit augmentation candidates (PerturbQA, Tahoe-100M).
2. [ ] **Survey Kaggle approaches** — prior Perturb-seq / cellular response
   winners + the current competition's public notebooks, Discussions, and
   shared writeups from other teams.
3. [ ] **Literature survey + `/wiki-ingest`** — agent harness, meta-learning,
   gene perturbation, scRNA-seq prediction (ongoing; runs in parallel with 1–2).
4. [ ] **Foundation model survey for Track C** — open <10B candidates (Qwen,
   Llama, Gemma, …). Tracks A/B are locked to GPT-OSS-120B.
5. [ ] **Draft track-specific approach plans + per-member action plan** —
   A: prompt engineering, B: agent + tool design, C: FT recipe; architecture
   decisions; who owns what.
6. [ ] **Wire up GPT-OSS-120B inference** (Together AI / Fireworks API per
   organizer reply).
7. [ ] **Build A/B shared data pipeline** (`data/raw/<track>/` → train/test
   loaders).
8. [ ] **First Track A submission baseline** (majority-class + a naive prompt).

## Completed

- [x] 2026-06-06 — `docs/scope-tracks`: scope tracks A/B/C and choose entry (PR #1).
- [x] Create shared Google Drive for papers/materials (7 subfolders seeded).
- [x] Create shared GitHub repo and invite Bing Hu + Joo Lee as collaborators.
