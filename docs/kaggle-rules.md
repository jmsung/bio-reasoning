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

**Reference numbers:** public-LB top ≈ 0.65; our leak-free evidence-prior
floor = **0.529** (LB) / 0.534 (local CV). See
[`challenge.md`](challenge.md#evaluation) for the full metric write-up.

**Submit:**

```bash
uv run kaggle competitions submit \
  -c ml-gen-x-bioreasoning-challenge-track-a \
  -f submissions/track_a_prior_baseline.csv -m "<message>"
```

## Track B / Track C

Placeholder — to be filled as we read the rules pages and submit. Each will
own: submission format, submission limits (per day / per team), external
data / model rules, compute limits, and gotchas discovered while submitting.
