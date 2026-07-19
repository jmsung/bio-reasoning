---
title: The self-improve loop's throughput block was a stale concurrency cap, not a deadlock — default 8→32 makes it runnable
type: findings
status: measured
cites:
  - methods/self-improvement-loop.md
---

[[../home]] | [[../index]]

# The self-improve loop was throughput-blocked by a stale concurrency cap

**Status: measured (2026-07-18, `fix/loop-concurrency-throughput`). Live run + isolated
concurrency benchmark.**

## Bottom line

Live self-improvement runs appeared to *hang* — at concurrency 8, a val-60 candidate took
**>17 min with zero completed trials** (connections stuck at ~2, ~0 CPU). It was **not a
deadlock and not the endpoint** — it was a **stale concurrency cap** throttling a
latency-bound workload. Raising the default from 8/16 → **32** makes the loop runnable: the
same run produced its **first journal entry in ~5.5 min** with connections saturating to **31**.

## What we measured

- **Endpoint is fine.** The loop's OpenRouter + gpt-oss path returns real completions; an
  isolated benchmark ran **16 parallel calls in 7.4 s and 32 in 10.5 s, both with 0 errors** —
  the OpenAI-compatible client (`Connection: close`) scales cleanly past the old bound.
- **gpt-oss-120b is a reasoning model** — each call generates a long reasoning trace (~7–10 s
  at `max_tokens 256`), so throughput is **concurrency-bound**, not latency-fixable per call.
  180 calls/candidate (val-60 × 3 seeds) ÷ 8 ≈ 17 min; ÷ 32 ≈ 5 min.
- **The old "c8/c16 deadlock bound" was stale** — it dated to a retired urllib keep-alive path
  (socket pileup → ThreadPoolExecutor deadlock, fixed with `Connection: close`). The current
  client has no such limit; 32 is safe (measured).
- **gpt-oss is free-tier on OpenRouter** — `$0 spent` is NOT a "no calls made" signal, which
  masked the diagnosis (looked like nothing was happening).

## Proof (live journal at concurrency 32, val-60, alphaevolve-reflect)

```
iter 1 | prior-rules prompt    | mean 0.562 ± 0.236 (de 0.539 / dir 0.586) → REJECTED
iter 2 | step-by-step mutation | mean 0.558 ± 0.059 (de 0.588 / dir 0.528) Δ+0.000 → REJECTED
       best-so-far 0.562   trajectory [0.562 → 0.558]
```

The loop reflects, mutates, scores ± band, and correctly rejects — DE noisy around the 0.555
wall, direction ~0.53–0.59, wide val-60 bands honestly logged. This is the legible
self-improving-system artifact running end-to-end.

## The fix

`scripts/self_improve_loop.py`: default `--concurrency` **16 → 32**. No other change needed —
the parallelism (ThreadPoolExecutor over the batched `infer_fn`) was already correct; it was
just under-fed. Closes the `loop-throughput-optimization` backlog item.

## Diagnostic lesson

Verify with `ps -p <pid>` (reliable), not `pgrep` (pattern-flaky — false "exited" several
times here). Smoke the endpoint with a single direct call before assuming a loop is broken.
`$0` on a free-tier model ≠ no work.
