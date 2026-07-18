# Predicting perturbation response under dual-OOD generalization

*BioReasoning Challenge 2026 — MLGenX Workshop @ ICLR 2026 (Genentech BRAID).*

**The question.** Given a genetic perturbation (a gene knocked down by CRISPRi)
and a target gene in mouse macrophages, can an LLM/agentic system predict whether
the target's expression goes **up**, **down**, or **none** — on a split where *both*
the perturbations *and* the target genes at test time are entirely unseen in training
(0/96 perturbations and 0/636 target genes overlap)? This **doubly-out-of-distribution**
design makes memorization worthless: a model cannot look up "what did this gene do
before" and must generalize from transferable biological reasoning. The scored metric
is `mean(AUROC_de, AUROC_dir)` — one axis for *does this pair respond at all* (DE), one
for *which direction* (up vs. down).

This repo is the full investigation: an honest evaluation harness, the modeling ladder,
and a rigorous characterization of exactly where signal exists and where it provably
does not.

## Key results

The central finding is a clean decomposition of the difficulty: **the DE axis is
provably unlearnable on this split; direction is the only learnable axis.** We reached
an honest, leak-free ceiling and — more importantly — established *why* it is a ceiling.

- **DE-vs-none is unlearnable by design, not merely un-cracked.** To rule out "our
  features are just weak," we built a **cheating oracle** — a DE head *permitted to see
  the true per-gene and per-perturbation DE propensities* — and scored it on the honest
  dual-OOD split. It still lands at **AUROC_de = 0.555 ± 0.036 ≈ chance**. Because an
  honest model can only do worse than an oracle, this is a hard upper bound: no leak-free
  channel — curated regulatory edges, learned models, retrieval lookup, chain-of-thought,
  or agentic external-knowledge retrieval — can rank none-vs-DE for a truly unseen pair.
  *Recognizing when the signal isn't there is the scientific contribution.*
  ([findings](knowledge/wiki/findings/de-unlearnable-oracle-ceiling.md))

- **Honest leak-free ceiling: Track A 0.586, Track B 0.597** (Kaggle public LB). Every
  leaderboard gain we booked was a **direction** gain; the DE axis never moved off chance.
  Direction tops out around **~0.65** (neighbour-retrieval AUROC_dir 0.651), giving an
  honest mean-AUROC ceiling near ~0.60.
  ([technical report](reports/technical-report.md))

- **The public leaderboard's 0.693 does not reproduce on an honest split.** A faithful
  implementation of the disclosed public recipe (char-ngram two-stage) scores only
  **0.552** on the real board — below our functional-feature model. The transductive
  tricks in the public notebooks move an OOD score by ≈0.000. We did not chase inflated
  numbers. ([findings](knowledge/wiki/findings/field-gap-586-693.md))

- **This sprint's capstone: external biological knowledge does not crack DE either.** A
  Track B **per-row LLM agent** reasoning over *live-retrieved* GO/STRING biology (the
  one format the oracle never saw — leak-free, 0% abstention) teased **AUROC_de = 0.631**
  on a 150-row read, then regressed to **0.578, 95% CI [0.549, 0.607]** on the trustworthy
  **1,500-row** read — an interval that *includes* the 0.555 ceiling. The wall is
  format-independent, and the 150-row tease would have been a false breakthrough had we
  submitted on it. ([findings](knowledge/wiki/findings/external-knowledge-does-not-crack-de.md))

The recurring methodological thread: **a rank-metric AUROC from a small OOD sample lies.**
A naive 60-row CV inflated Track B by **0.187** (0.675 CV → 0.488 LB) and *inverted* a
conclusion; our honest dual-OOD split predicts the real leaderboard to within **~0.004–0.005**
and became the trusted offline gate we rank every idea on before spending a Kaggle submission.

## What's technically interesting

- **A leak-free dual-OOD evaluation harness** ([`eval/split.py`](src/bio_reasoning/eval/split.py))
  — holds perturbations *and* target genes out simultaneously, mirroring the test set's
  structure, so offline scores actually predict the board. This discipline is the keystone
  the whole project rests on.
- **A cheating-oracle ceiling probe** ([`eval/de_ceiling.py`](src/bio_reasoning/eval/de_ceiling.py),
  [`scripts/de_ceiling_probe.py`](scripts/de_ceiling_probe.py)) — the falsification tool
  that turns "we couldn't crack DE" into "DE is unrankable even by a model allowed to cheat,"
  after catching and defusing a subtle intra-fold label-leakage trap (a mirage 0.960).
- **A self-evolving agentic optimization loop** ([`trial_loop/`](src/bio_reasoning/trial_loop/))
  — AlphaEvolve/GEPA/ACE-style search: a population of variants under reflection-driven
  mutation that reasons over misclassified cases
  ([`reflective_mutation.py`](src/bio_reasoning/trial_loop/reflective_mutation.py),
  [`evolve.py`](src/bio_reasoning/trial_loop/evolve.py)) plus a scored fusion-config axis
  ([`config_predictor.py`](src/bio_reasoning/trial_loop/config_predictor.py)), each iteration
  logged to a legible per-iteration journal
  ([`journal.py`](src/bio_reasoning/trial_loop/journal.py)) so you can see whether the search
  is improving or random-walking.
- **A calibrated retrieval agent** — a per-row Track B agent that pulls GO:BP terms and STRING
  partners live from mygene.info / string-db, with the abstention collapse that sank v1 (72%
  `0/0` ties → LB 0.488) fixed to 0%.

Full writeup: [`reports/technical-report.md`](reports/technical-report.md).

## Approach

We run this project **agentically**: the whole investigation above was built by directing
agents — define the goal, shape the plan, review the diffs — not by hand-writing the code.
It is deliberate practice in agent-driven engineering on a biologically meaningful problem,
with a bias toward system-level tooling (an honest harness, a self-improving loop) over
hand-tuning. Full philosophy + agent conventions: [`.claude/CLAUDE.md`](.claude/CLAUDE.md).

## Team

- Jongmin Sung — https://www.linkedin.com/in/jongmin-sung/
- Bing Hu — https://www.linkedin.com/in/bingxuhu/
- Joo Lee — https://www.linkedin.com/in/joo-lee-b0a9b9161/

## Repo tour

```bash
uv sync    # install deps
```

Start with [`reports/technical-report.md`](reports/technical-report.md) for the full story,
then the canonical docs:

| File | Owns |
|---|---|
| [`reports/technical-report.md`](reports/technical-report.md) | The full investigation — problem, methods, results, negative results |
| [`docs/challenge.md`](docs/challenge.md) | Challenge summary, per-track detail, entry decision |
| [`docs/roadmap.md`](docs/roadmap.md) | Single living plan — priority-ordered Todo + completed milestones |
| [`docs/development.md`](docs/development.md) | Setup, provider config, GPT-OSS serving, R&D workflow, conventions |
| [`docs/architecture.md`](docs/architecture.md) | System design — data flow, components, per-track notes |
| [`docs/where-things-live.md`](docs/where-things-live.md) | Map of repo / Drive / Kaggle |
| [`knowledge/wiki/`](knowledge/wiki/) | Distilled team knowledge — findings, methods, decisions |

Code layout: importable library in `src/bio_reasoning/`, entry points in `scripts/`. Data is
pulled from Kaggle, not committed. Full setup detail (provider config, local GPT-OSS/vLLM
serving, smoke tests) lives in [`docs/development.md`](docs/development.md).

## Resources

- **GitHub:** https://github.com/jmsung/bio-reasoning
- **Kaggle:**
  [Track A](https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-a) ·
  [Track B](https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-b)
- **Challenge overview:** https://genentech.github.io/BioReasoningChallenge/

## License

MIT — see [`LICENSE`](LICENSE).

## Source of truth

`README.md` and `docs/` are the authoritative reference for this repo. Any code change that
affects workflow, API, file layout, data schema, or commands **must** update the relevant docs
in the same commit or PR. Stale docs are worse than missing docs.
</content>
