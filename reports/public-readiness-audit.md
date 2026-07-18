# Public-readiness audit — `bio-reasoning` (cb)

**Date:** 2026-07-17 · **Branch:** `chore/public-audit` · **Scope:** full git history + working tree
**Purpose:** safety audit before flipping the repo from PRIVATE → PUBLIC as a job-application showcase.

**Verdict: SAFE-AFTER-FIXES.** No secrets in history or tree (blocking gate PASSED). The
low-risk fixes in this PR (mb-path scrub, MIT LICENSE) are applied. One **non-technical**
gate remains: **timing** — recommend flipping *after* the 2026-07-22 competition deadline.

---

## 1. Secrets — history + tree (BLOCKING GATE: PASSED)

Scanned **all 133 commits** across every ref (`git log --all -p -G <pattern>`) plus the working
tree for: OpenAI `sk-`, Anthropic `sk-ant-`, OpenRouter `sk-or-v1-`, `ghp_`, `xox*`, `AKIA…`
(AWS), `AIza…` (Google), `glpat-`, `Bearer …`, `BEGIN … PRIVATE KEY`, and hardcoded
`api_key=`/`password=` literals.

- **No real secret found in tree or history.** The only pattern hits are harmless:
  - `tests/conftest.py` (commit `03d4678`): `monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")` — a **test fixture**, not a real key.
  - `src/bio_reasoning/utils/llm_clients.py`: `"local-vllm-placeholder-key"`, `"ollama"` — **placeholder** strings for keyless local endpoints.
- **`.env` / `.env.local` were NEVER committed** — confirmed across all history; only `.env.example` is (and ever was) tracked. In the worktree they exist only as **gitignored symlinks** to the real cb copies.
- **All client/agent files read keys from the environment**, not literals: `src/bio_reasoning/utils/{llm_clients,anthropic_client,openai_client,openai_compat}.py`, `scripts/track_b_retrieval_agent.py`, etc. all use `os.getenv(...)`. Verified — zero embedded credentials.
- **`.gitignore`** covers `.env`, `.env.local`, and gitignores `.mb`; `git check-ignore` confirms all three are ignored. No gitignore gap found — **no hardening needed**.

**Result: the blocking gate is clean. Nothing sensitive is exposed by making history public.**

## 2. mb / private-content leak (FIXED)

cb is the public artifact; `mb/` (strategy, spend, planning notes) is private. Scan found
**no pasted private content** — only **dangling path citations** pointing readers at private
`mb/…` files that won't exist in a public clone.

**Scrubbed (this PR):**
- `docs/perturb-seq-lane-decision.md` — 5 `mb/active/…` and `mb/notes/…` citations removed/replaced (the doc's own content is the source; branch names already cited). The decision content itself is competition-score material, which is team-shareable in cb (per team policy), so only the private-dir pointers were removed, not the analysis.
- `scripts/char_ngram_ensemble_ood_val.py` — one `mb/notes/rank1-plan.md` comment reference genericized to "internal planning notes."

**Left as-is (correct):** `.claude/skills/{commit,pr-open,pr-merge}/SKILL.md` and
`knowledge/wiki/decisions/0001-pr-workflow.md` mention the *pattern* `mb/active/<slug>.md`
as part of documenting the team's PR tooling. These are generic workflow descriptions, **not**
private-content pointers, and are meaningful to a public reader evaluating the agentic workflow.

## 3. PII / personal / internal paths

- **Absolute `/Users/jmsung/…` paths in tracked content: NONE.** Clean.
- **Personal emails (gmail/outlook/etc.): NONE** in tracked files.
- **Teammate info:** only the three public LinkedIn URLs already in `README.md` / `.claude/CLAUDE.md` (Jongmin Sung, Bing Hu, Joo Lee). No private contact info. Low risk — these are intentionally public professional profiles; flag for teammate awareness only.
- **Google Drive folder link** appears in 6 tracked files (`README.md`, `.claude/CLAUDE.md`, `docs/where-things-live.md`, `knowledge/wiki/{README,home}.md`). This is a **shared team Drive folder URL**. Exposure risk depends on the folder's own Drive sharing settings, not the repo — if it is restricted-access (likely), publishing the URL is low risk (no access without permission). **Recommendation (not auto-fixed — needs Jongmin's call):** confirm the Drive folder is *not* "anyone with the link", or replace the links with a note before flipping. Left in place because removing a documented team resource is a judgment call, not a trivially-safe fix.

## 4. Competition sensitivity — TIMING (the real remaining gate)

The Kaggle competition deadline is **2026-07-22 07:00 UTC (~5 days out)**; the repo would go
public *during* an active competition.

- `docs/kaggle-rules.md` documents the augmentation-data allowance (PerturbQA, Tahoe-100M) but the authoritative external-code-sharing / private-sharing rules live on the JS-rendered Kaggle Rules tab, which is not machine-fetchable here. Many Kaggle competitions require that any shared code/method be made available **equally to all participants via the official forum**, and restrict *private* sharing among a subset — a public GitHub repo sits in an ambiguous zone relative to that norm.
- **Competitive value of publishing now is low:** standing is mid-pack (A 0.586 / B 0.597, both far below the 0.693 / 0.752 leaders) and the substantive findings are **negative results** (perturb-seq lane closed, DE-vs-none dead, char-ngram dead). There is little a competitor could weaponize.
- **But there is zero upside to flipping now vs. in 6 days.** A job-showcase repo does not need to be public *this specific week*.

**Timing recommendation: wait until AFTER the 2026-07-22 deadline to flip public.** It removes
all ambiguity about competition rules at no cost. If Jongmin wants it public sooner, the
residual risk is low (given mid-pack standing + negative-result findings) but non-zero on the
rules-compliance axis — his call, but the clean recommendation is to wait.

## 5. Showcase readiness (polish, non-blocking)

- **LICENSE — ADDED (this PR):** MIT, © 2026 Jongmin Sung, referenced from a new `## License` section in `README.md`. (License choice confirmed by Jongmin.)
- **README:** strong showcase entry point — clear project framing, agentic-engineering philosophy, "where to start", setup, script organization, canonical-docs map. No changes needed beyond the license reference. *Minor optional polish (not done — non-trivial, recommend only):* the "Local GPT-OSS-120B setup" section (README L188–204) contains machine-specific status ("Hugging Face token: not configured yet", a specific GPU) that reads as stale working-notes for a public audience; and the "Recommended next cleanup" section reads as aspirational scaffolding. Neither is a leak — cosmetic only.
- **TODO/FIXME/dead scaffolding:** effectively none — a single false-positive hit (`band=X.XXX` docstring). Clean.
- **CI:** `.github/workflows/guard-main.yml` is benign (enforces PR-squash-merge subjects); no secrets.

---

## What was fixed in this PR

1. Added `LICENSE` (MIT, © 2026 Jongmin Sung) + `## License` section in `README.md`.
2. Scrubbed 5 private `mb/…` path citations from `docs/perturb-seq-lane-decision.md`.
3. Genericized 1 `mb/notes/…` reference in `scripts/char_ngram_ensemble_ood_val.py`.

## Residual risks (none blocking; Jongmin's call)

- **Timing** — flipping during the active competition (see §4). *Recommend waiting until after 2026-07-22.*
- **Google Drive folder link** exposed in 6 files (§3) — verify the folder isn't world-readable, or strip the links.
- **Teammate LinkedIn URLs** are public by nature but two co-authors' profiles become associated with this repo publicly — a courtesy heads-up, not a safety issue.

## Public-safe verdict

**SAFE-AFTER-FIXES.** No secret or private content is exposed by the code/history. The fixes in
this PR close the mb-path and licensing gaps. The remaining decision is **timing**, not safety:
the recommendation is to **flip after the 2026-07-22 competition deadline**, and to confirm the
Drive folder's sharing setting beforehand.
