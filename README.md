# bio-reasoning-2026

BioReasoning Challenge 2026 — MLGenX Workshop @ ICLR 2026.

Testing whether LLMs and agentic systems can serve as useful computational
engines for predicting cellular behavior. Specifically: predict perturbation
outcomes in macrophages across three challenge tracks
([overview](https://genentech.github.io/BioReasoningChallenge/)).

## Team
- Jongmin Sung — https://www.linkedin.com/in/jongmin-sung/
- Bing Hu — https://www.linkedin.com/in/bingxuhu/
- Joo Lee — https://www.linkedin.com/in/joo-lee-b0a9b9161/

## Approach

We're running this project **agentically**: we plan, guide, and review;
the agent does most of the actual code work. The point is hands-on
practice with agent-driven engineering on a biologically meaningful problem
in a low-stakes setting. Concretely:

- **Agents do the work, we manage.** Define goals, shape the plan, review
  diffs, give feedback. The agent executes under our direction.
- **Agents must ask.** When intent is ambiguous, stop and ask — alignment
  beats velocity.
- **System over micro-management.** Cutting-edge harness and agentic
  workflows over hand-tuning.

(Full philosophy + agent conventions: [`.claude/CLAUDE.md`](.claude/CLAUDE.md))

## Where to start

If you just cloned this repo:

1. Skim [`docs/challenge.md`](docs/challenge.md) — what the challenge is,
   tracks, our entry decision.
2. Skim [`docs/where-things-live.md`](docs/where-things-live.md) — repo
   vs. Drive vs. Kaggle.
3. Point your Claude Code (or any agent) at [`.claude/CLAUDE.md`](.claude/CLAUDE.md) —
   team-shared conventions and skills.

## Setup

```bash
uv sync                 # install deps
cp .env.example .env    # add API keys (Together AI / Fireworks for GPT-OSS-120B; Kaggle)
```

For this repo's current multi-provider testing flow, a repo-local virtualenv is
also supported:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
python -m pip install anthropic openai python-dotenv pandas scikit-learn "dspy>=3.1.3" "azure-identity>=1.23.0" vllm
```

Data is pulled from Kaggle, not committed. See `data/README.md` for
download instructions once `scripts/prepare_data.py` is wired up.

## Script organization

The repo is currently organized around three execution layers:

### 1. Main challenge runners
- `scripts/track_a_prompt_only.py` — main Track A runner
- `scripts/track_b_agentic.py` — main Track B runner

These are the scripts to evolve toward full challenge submissions.

Shared, importable pieces live under `src/bio_reasoning/`: the runners' agent
wiring (`build_openrouter_lm`, `build_react_agent`, `predict_row` in
`track_b_agentic.py`) and the OpenAI-compatible chat client
(`src/bio_reasoning/utils/openai_compat.py`, `post_chat_completion`) are reused
by the trial-loop below.

### 1b. Trial-loop optimization harness
- `scripts/trial_loop.py` — CLI to score Track A prompt variants (`--track a`,
  default) or the Track B agent (`--track b`) on the leak-free dual-OOD
  validation split, then propose → run → reflect → archive over a grid.
- `src/bio_reasoning/trial_loop/` — the importable harness (loop, reflect,
  archive, types).
- `scripts/self_improve_loop.py` — the 24/7 self-improvement runner: propose →
  triple-verify (a candidate must beat baseline on every OOD split by more than
  the seed noise band; when a Traxler real-label fold is supplied, an OOD-survivor
  must *also* beat baseline on that held-out in-domain fold) → promote, until dry
  or budget-capped. Two lanes share the gate: the default **DE-votes** lane (live
  prompt variants, KB-ruled-out channels filtered; search policy via
  `--proposer {grid,bandit,llm}`) and the **agentic** lane (`--agentic`) that
  searches Track B tool configs — which real-data tools (GO/STRING/Traxler
  direction) a per-variant ReAct agent may call — with the tool-free agent as
  baseline (leak-safe: the Traxler tool is dropped whenever its fold is the eval).
  It never submits — a gate-surviving variant is surfaced for a human-gated
  Kaggle submission.
  Backed by `trial_loop.{inference,proposers,de_variants,bandit,llm_proposer,agent_variants,tools,gate,ruled_out,driver,submission,preflight}`.
- `make verify` — fast DEV pipeline (minutes, not the ~1.4–2.8 h full-val gate):
  `scripts/verify_loop.py` preflights one real smoke trial on a `--val-n` subsample
  (asserts non-empty responses, `n_val>0`, non-nan mean, a written archive — liveness ≠
  working), then `scripts/self_improve_loop.py --val-n N` prints a `DEV SIGNAL READ`
  (baseline vs best-variant Δ) as a go/no-go. The `--val-n` knob is DEV-ONLY and makes the
  gate untrustworthy — never promote off it. Tune with `make verify VAL_N=120 MAX_TRIALS=8`.
- `scripts/build_traxler_labels.py` — regenerates the Traxler native real-label
  validation fold (`data/external/traxler_labels.csv`, gitignored — a reproducible
  artifact like `train.csv`) that the gate's optional external check scores against.
  Backed by `data.traxler_labels` (log2FC→schema thresholding + a leak-free exemplar pool).

Artifacts (`trials.jsonl`, leaderboard, per-row cache) are written to
`outputs/trial-loop/`; self-improve trials to `outputs/self-improve-loop/`
(both gitignored). Track B needs the `track-b` dep group
(`uv sync --group track-b`) and `OPENROUTER_API_KEY`.

### 2. Track B tools
- `scripts/tools/` — local and external tool implementations used by Track B

Recommended rule: keep reusable tool logic in `scripts/tools/`, not embedded
inside agent runner scripts.

### 3. Smoke / validation scripts
- `scripts/smoke/provider_smoke.py` — quick provider ping
- `scripts/smoke/track_schema_smoke.py` — minimal Track A / Track B schema validation
- `scripts/smoke/common.py` — shared provider-selection + request helpers

Recommended rule: keep smoke tests lightweight, provider-aware, and focused on
connectivity + output schema rather than full evaluation quality.

## Provider configuration

Provider selection is controlled by `.env` via:

```env
BIOREASONING_LLM_PROVIDER=openai_compatible  # or: openai, azure_openai, anthropic
```

Supported modes currently include:

- `openai_compatible` — local vLLM / GPT-OSS or other OpenAI-compatible endpoints
- `openai` — OpenAI-hosted models
- `azure_openai` — Azure OpenAI or Azure AI Foundry / OpenAI-compatible endpoints
- `anthropic` — Anthropic-hosted models

The smoke scripts also accept a `--provider` override:

```bash
--provider gpt_oss
--provider openai
--provider azure
--provider anthropic
```

## Smoke tests

### Quick provider ping

```bash
. .venv/bin/activate
python scripts/smoke/provider_smoke.py --provider azure --prompt 'Reply with exactly: smoke test ok'
```

### Track A schema smoke test

```bash
. .venv/bin/activate
python scripts/smoke/track_schema_smoke.py --provider azure --track a --rows 1 --max-tokens 64
```

### Track B schema smoke test

```bash
. .venv/bin/activate
python scripts/smoke/track_schema_smoke.py --provider azure --track b --rows 1 --max-tokens 64
```

Outputs are written to:

- `outputs/smoke/track_a_<provider>_smoke_submission.csv`
- `outputs/smoke/track_b_<provider>_smoke_submission.csv`

## Local GPT-OSS-120B setup

Tracks A and B in the official challenge use GPT-OSS-120B via a local vLLM
server.

### What is already verified in this repo

- `vllm` is installed in `.venv`
- the local vLLM OpenAI API server CLI is available
- Azure smoke tests are passing
- provider-aware smoke scripts are ready to test GPT-OSS once the server is up

### What is still required on this machine

To pull `openai/gpt-oss-120b`, this node still needs a Hugging Face token.
Current status on this machine during validation:

- CUDA-visible GPU present: `NVIDIA GB10`
- disk available: ~660 GB free on `/`
- Hugging Face token: **not configured yet**

Without HF auth, the model download cannot start.

### Recommended serve command

```bash
. .venv/bin/activate
export HF_HOME=${HF_HOME:-$HOME/.cache/huggingface}
python -m vllm.entrypoints.openai.api_server \
  --model openai/gpt-oss-120b \
  --port 8000 \
  --enforce-eager \
  --no-enable-prefix-caching
```

If you need tensor parallelism across multiple GPUs, add:

```bash
  --tensor-parallel-size 2
```

### After the local server starts

Run GPT-OSS smoke tests with:

```bash
. .venv/bin/activate
BIOREASONING_LLM_PROVIDER=openai_compatible \
BIOREASONING_OPENAI_API_BASE=http://localhost:8000/v1 \
BIOREASONING_OPENAI_MODEL=openai/gpt-oss-120b \
python scripts/smoke/provider_smoke.py --provider gpt_oss --max-tokens 64
```

```bash
. .venv/bin/activate
BIOREASONING_LLM_PROVIDER=openai_compatible \
BIOREASONING_OPENAI_API_BASE=http://localhost:8000/v1 \
BIOREASONING_OPENAI_MODEL=openai/gpt-oss-120b \
python scripts/smoke/track_schema_smoke.py --provider gpt_oss --track a --rows 1 --max-tokens 64
```

```bash
. .venv/bin/activate
BIOREASONING_LLM_PROVIDER=openai_compatible \
BIOREASONING_OPENAI_API_BASE=http://localhost:8000/v1 \
BIOREASONING_OPENAI_MODEL=openai/gpt-oss-120b \
python scripts/smoke/track_schema_smoke.py --provider gpt_oss --track b --rows 1 --max-tokens 64
```

### Recommended next cleanup

As the repo matures, the cleanest layout is:

- `scripts/run/` — primary Track A / Track B runners
- `scripts/tools/` — Track B tools
- `scripts/smoke/` — provider and schema smoke tests
- `src/bio_reasoning/utils/` — reusable provider clients / config

That keeps submission logic, tools, smoke tests, and reusable library code
separated cleanly.

## Canonical docs

| File | Owns |
|---|---|
| [`docs/challenge.md`](docs/challenge.md) | Challenge summary, per-track detail, entry decision |
| [`docs/roadmap.md`](docs/roadmap.md) | Single living plan — priority-ordered Todo + completed milestones |
| [`docs/development.md`](docs/development.md) | Setup, R&D workflow, conventions |
| [`docs/where-things-live.md`](docs/where-things-live.md) | Map of repo / Drive / Kaggle and a "what goes where" cheatsheet |
| [`knowledge/wiki/`](knowledge/wiki/) | Distilled team knowledge — see its [README](knowledge/wiki/README.md) for the four `/wiki-*` skills |
| [`.claude/CLAUDE.md`](.claude/CLAUDE.md) | Agent-facing team conventions |

## Resources

- **GitHub:** https://github.com/jmsung/bio-reasoning
- **Drive** (papers, raw artifacts, writeups): https://drive.google.com/drive/folders/1kE-JCKUJowtu7XFn5LALDt9xEq1DYBxS
- **Kaggle:**
  [Track A](https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-a) ·
  [Track B](https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-b) ·
  [Track C](https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-c)

## Source of truth

`README.md` and `docs/` are the authoritative reference for this repo.
Any code change that affects workflow, API, file layout, data schema, or
commands **must** update the relevant docs in the same commit or PR.
Stale docs are worse than missing docs.
