# Kaggle rules

Submission format, competition rules, and gotchas for the three tracks.

Authoritative source is the Kaggle "Rules" tab for each track — links in
[`challenge.md`](challenge.md). This page is our distilled, team-facing
working notes, not a replacement for the official rules.

## Track A

**Metric — `mean(AUROC_de, AUROC_dir)`, not accuracy.** Confirmed from the
vendored official scorer
[`src/bio_reasoning/eval/kaggle_metric_track_a.py`](../src/bio_reasoning/eval/kaggle_metric_track_a.py):

- **AUROC_de** ranks none-vs-DE by `prediction_up + prediction_down`.
- **AUROC_dir** ranks up-vs-down by `prediction_up / (prediction_up + prediction_down)`
  over DE-positive rows only.

**Consequence: predictions must be graded floats**, not hard labels — the
metric ranks by score, so a hard `up`/`down`/`none` throws away the ranking
signal. A constant "predict none" scores ≈ **0.5**; the 0.553 majority-class
figure is an *accuracy* reference and does **not** apply here.

**Submission columns** (15) — match the sample header exactly:

```
id, prediction_up, prediction_down,
prediction_up_seed42, prediction_down_seed42,
prediction_up_seed43, prediction_down_seed43,
prediction_up_seed44, prediction_down_seed44,
reasoning_trace_seed42, reasoning_trace_seed43, reasoning_trace_seed44,
tokens_used, prompt_tokens, model_name
```

- One row per `test.csv` id (1,813 rows). `id` is `<pert>_<gene>`.
- Three seeds (42/43/44) carry per-seed predictions + reasoning traces; a
  deterministic model repeats the same values across seeds.
- **Prompt-token cap: 4,096.** `tokens_used` / `prompt_tokens` are reported
  per submission.

**Reference numbers:** public-LB top ≈ 0.693 (2026-07); our leak-free evidence-prior
floor = **0.529** (LB) / 0.534 (local CV). See
[`challenge.md`](challenge.md#evaluation) for the full metric write-up.

**Submit:**

```bash
uv run kaggle competitions submit \
  -c ml-gen-x-bioreasoning-challenge-track-a \
  -f submissions/track_a_prior_baseline.csv -m "<message>"
```

## Track B — agentic tool-use

Same task, data, metric, and submission math as Track A — only the modeling
constraints differ. Authoritative source is the Kaggle Track B "Rules" tab
(JS-rendered, not machine-fetchable); the below is distilled from
[`challenge.md`](challenge.md#track-b--multi-agentic-tool-use) and
[`../knowledge/source/2026-bioreasoning-challenge-overview.md`](../knowledge/source/2026-bioreasoning-challenge-overview.md).

**Constraints:**

- **Fixed base model: GPT-OSS-120B** (same as A); **fine-tuning the base is forbidden**.
- **Tools: ≤ 100 distinct tools, ≤ 250 tool calls per test row.**
- **Prompt-token cap: 16,384** (4× Track A).
- **No web access / no external LLMs at inference.**
- **Traces required** — submissions must carry tool-call traces for audit / reproducibility.
- **Allowed data augmentation (all tracks):** public perturbation datasets
  PerturbQA, Tahoe-100M (permissively licensed).

**Submission** — the same 15-column schema as Track A, plus the tool-definition /
trace metadata (reasoning traces, `tokens_used`, tool usage, model info). One row
per `test.csv` id (1,813).

**Is an ML-model-backed tool (e.g. TabPFN) allowed? — Probably yes; confirm on the
Rules tab.** The only model restrictions are (a) the base LLM is fixed and
non-fine-tunable, and (b) "no external **LLMs** at inference." A frozen, in-context
**tabular** foundation model (TabPFN / TabICL) is neither the base LLM, a fine-tune
of it, nor an external *LLM* — it is a local computational tool, and tools are
explicitly allowed (≤ 100). So a `tabpfn_predict(pert, gene)` tool reads as legal.
**Caveat:** the authoritative Kaggle Track B rules tab is JS-rendered and unread
here; the challenge-overview wording bars external *LLMs* specifically, not all
auxiliary models. Confirm the rules tab explicitly permits offline / precomputed
models as tools before relying on it. See
[`tabpfn-for-perturbation-tracks`](../knowledge/wiki/findings/tabpfn-for-perturbation-tracks.md)
and [`competitor-landscape`](../knowledge/wiki/findings/competitor-landscape.md).

**Reference numbers:** public-LB top = **0.752** (cellshift.bio, 2026-07); our
agentic attempt = **0.488** (below the 0.529 Track A floor — abstention collapse,
PR #13, see
[`track-b-abstention-failure`](../knowledge/wiki/findings/track-b-abstention-failure.md)).

## Track C — fine-tuning

- **Open model < 10B params** (e.g. Qwen3-4B-Thinking, Gemma); **any fine-tuning
  technique** (SFT, LoRA, RL, process reward models, best-of-N).
- **No tools, no web, no external LLMs at inference.**
- Same task / metric / submission math as A and B.
- **Reference:** public-LB top = **0.693** (2026-07). Not entered by us.
