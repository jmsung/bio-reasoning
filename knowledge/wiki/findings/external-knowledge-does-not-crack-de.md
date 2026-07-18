---
title: External biological knowledge does not crack the DE axis — LLM-agent retrieval lands at parity; the DE wall is format-independent
type: findings
status: measured
cites:
  - findings/retrieval-agent-de-headline-was-noise.md
  - findings/coessentiality-direction-key-negative.md
  - findings/de-unlearnable-oracle-ceiling.md
  - findings/de-unlearnable-on-dual-ood.md
  - findings/field-gap-586-693.md
  - findings/neighbor-retrieval-direction-lever.md
---

[[../home]] | [[../index]]

# External knowledge does not crack the DE axis — the wall is format-independent

**Status: measured — leaderboard sprint 2026-07-18 (`feat/depmap-coessentiality-dir` #71,
`feat/track-b-retrieval-agent` #72, `feat/track-b-full-read` #74). Closed with decision A:
bank the honest ceiling (Track A 0.586, Track B 0.597). No Kaggle quota spent.**

The recurring escape hatch for the DE-unlearnable result ([[de-unlearnable-oracle-ceiling]],
[[de-unlearnable-on-dual-ood]]) was always *format*: every DE kill so far used a **static**
signal source — curated edges, learned heads, retrieval lookup, chain-of-thought — that the
leakage-allowed oracle (0.555) roughly bounds. The one untried format was **external biology
delivered live, as an LLM agent reasoning over retrieved knowledge the oracle never saw.** If
any format could beat 0.555, it was this one. The sprint fired it. It landed at **parity, not
above** — so the DE ceiling is now confirmed **format-independent**.

## The two levers, both null

| lever | what it added | result | verdict |
|---|---|---|---|
| DepMap co-essentiality direction key ([[coessentiality-direction-key-negative]]) | a *better neighbour key* for DIR (fitness-correlation modules vs STRING edges) | standalone DIR-AUROC **0.547 ± 0.048** « STRING 0.651; fused **0.637** (Δ−0.014, drags down) | weaker key; ~0.65 DIR ceiling holds |
| Track B external-knowledge retrieval agent ([[retrieval-agent-de-headline-was-noise]]) | per-row LLM agent over retrieved GO/STRING, calibrated (0% abstention) | DE 150-row **0.631** → 1500-row **0.578** [0.549, 0.607]; fused **0.604 ± 0.035** vs 0.597 incumbent | leak-free; DE parity, not a break |

Neither cleared its incumbent. The direction key was *weaker* than STRING; the DE agent was
*at parity*. Both were killed offline on the trustworthy dual-OOD surface — no submission.

## Why this is the strong form of the DE result

The retrieval agent had every structural advantage a DE-cracker could want: (i) it reads
**external, label-free** GO:BP + STRING biology, so it is not bounded by the identity/marginal
oracle; (ii) it is **leak-free** (no label-fitted component; dual-OOD `assert_leak_free`
enforced); (iii) it is **calibrated** — 0% abstention, so it does not repeat the v1
abstention collapse ([[neighbor-retrieval-direction-lever]] context: 72%-`0/0` → LB 0.488).
Given all three, its honest DE read still sits at **0.578, CI [0.549, 0.607]** — the interval
*includes* the 0.555 identity/marginal ceiling. External biology, in its strongest deliverable
form, carries **at most a whisper** of transferable DE signal, nowhere near the field's 0.693.

Combined with the [[field-gap-586-693]] probe (the public recipe doesn't reproduce; transductive
tricks are ≈0 on OOD), the picture is closed: **there is no reachable DE signal — internal,
external, static, or agentic.**

## The noise-vs-signal lesson (reinforced, third time)

The 150-row AUROC_de = 0.631 was **small-sample noise**: per-seed DE swung 0.533 → 0.616 across
the 3 × 500-row seeds, a ±0.04 band straddling chance. This is the same trap that produced 0.675
on a 60-row CV (→ LB 0.488) and 0.72 on the PerturbQA overlap gate (→ chance on OOD). **A
rank-metric AUROC from < ~500 dual-OOD rows is not trustworthy;** gate any "we beat the ceiling"
claim on ≥ 500 rows × multi-seed. Had we submitted on the 150-row tease, it would have been a
false breakthrough on the public board.

## Implications

1. **DE-vs-none is unlearnable on this dual-OOD task by every method available** — curated
   edges, learned models, retrieval lookup, chain-of-thought, and now agentic external-knowledge
   retrieval all land at ~0.55. The negative is format-independent.
2. **The ~0.65 direction ceiling holds** — a fresh, diverse key (co-essentiality) is weaker than
   STRING, not better; the better-key search for DIR is not exhausted but co-essentiality is out.
3. **Honest ceiling banked:** Track A 0.586, Track B 0.597. The sprint's value is epistemic — it
   closes the last open lever and hardens the headline negative rather than denting it.
