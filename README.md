# bio-reasoning-2026

BioReasoning Challenge 2026 — MLGenX Workshop @ ICLR 2026.

Testing whether LLMs and agentic systems can serve as useful computational engines for predicting cellular behavior.

## Challenge

Three tracks (see https://genentech.github.io/BioReasoningChallenge/):

- **Track A** — Prompt-only (no tools, single call). Fixed base: GPT-OSS-120B. Max 4,096 prompt tokens, 3 samples per question.
- **Track B** — (Multi-)agentic tool-use. Fixed base: GPT-OSS-120B. Max 100 tools, 250 calls, 16,384 prompt tokens. Traces required.
- **Track C** — Fine-tuning (reasoning, no tools). Open model < 10B params; any FT technique.

Likely entering A and/or B.

## Setup

```bash
uv sync
```

## Layout

- `src/bio_reasoning/` — library code
- `scripts/` — entry points and orchestration
- `notebooks/` — exploration
- `tests/` — pytest
- `docs/` — team-facing docs (architecture, design notes)
