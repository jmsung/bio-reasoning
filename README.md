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

Data is pulled from Kaggle, not committed. See `data/README.md` for
download instructions once `scripts/prepare_data.py` is wired up.

## Canonical docs

| File | Owns |
|---|---|
| [`docs/challenge.md`](docs/challenge.md) | Challenge summary, per-track detail, entry decision |
| [`docs/where-things-live.md`](docs/where-things-live.md) | Map of repo / Drive / Kaggle and a "what goes where" cheatsheet |
| [`docs/wiki/`](docs/wiki/) | Distilled team knowledge — see its [README](docs/wiki/README.md) for the four `/wiki-*` skills |
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
