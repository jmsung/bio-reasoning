---
title: cellshift.bio 0.752 forensics — the Track B leader's edge is most plausibly a data moat, not a rules-legal lever
type: findings
status: draft
cites:
  - findings/competitor-landscape.md
  - findings/external-knowledge-does-not-crack-de.md
  - findings/de-unlearnable-on-dual-ood.md
  - findings/de-unlearnable-oracle-ceiling.md
  - findings/direction-transfers-de-doesnt.md
  - findings/dir-ceiling-equal-weight-fusion.md
  - findings/field-gap-586-693.md
  - findings/tabpfn-for-perturbation-tracks.md
---

[[../home]] | [[../index]]

# cellshift.bio 0.752 forensics — data moat, not a lever we can turn

**Status: draft — web-research probe 2026-07-17 (`research/cellshift-forensics`), no spend,
no Kaggle submit. Forensic read on why cellshift.bio leads Track B at 0.752 vs our honest
ceiling (B 0.597), and whether any of it is a rules-legal lever we could still try before the
2026-07-22 07:00 UTC deadline (~4 days).**

Bottom line: cellshift.bio is **most plausibly Shift Bioscience** — an AI-Virtual-Cell
perturbation-biology company whose whole moat is **large-scale proprietary perturb-seq /
scRNA-seq data**. The single most-plausible explanation of 0.752 is therefore a **data
advantage used as an agent tool** (real measured DE/direction for near-test perturbations),
not a clever method — i.e. **a moat we cannot cheaply replicate**, with a real chance the
number is also partly **public-LB-inflated** like the unreproducible 0.693 Track A pack
([[field-gap-586-693]]). Every rules-legal, still-untried lever we enumerated meets our
already-measured walls (DE unlearnable, oracle 0.555, [[de-unlearnable-oracle-ceiling]];
direction capped ~0.65, [[dir-ceiling-equal-weight-fusion]]). **Verdict: 0.752 is honestly
out of reach for us in 4 days; do not sprint to chase it.**

## Who is cellshift.bio? (web, cited — strong inference, not confirmed 1:1)

The domain `cellshift.bio` is **Cloudflare-403 to our fetch** and the Kaggle Track B
leaderboard is JS-rendered (unfetchable), so we could **not** directly confirm the team's
identity or read a disclosed method. On name + domain + domain-of-expertise, the overwhelming
match is **Shift Bioscience** (Cambridge UK + Toronto; founded 2017, Daniel Ives / Brendan
Swain):

- Builds an **AI Virtual Cell** platform for **genetic-perturbation-response prediction**
  (up/down-regulation of genes) from **large-scale proprietary multiomic / scRNA-seq datasets**;
  benchmarks on **14 perturb-seq datasets** with rank-based + DEG-aware metrics.
  [shiftbioscience.com/science](https://shiftbioscience.com/science/),
  [metric-calibration release](https://shiftbioscience.com/shift-bioscience-publishes-improved-metric-calibration-framework-for-robust-genetic-perturbation-modeling-using-ai-virtual-cells/)
- Deep foundation-model bench: Head of ML **Lucas Camillo**; advisor **Bo Wang** (Toronto —
  scGPT / single-cell foundation models). [$16M raise](https://shiftbioscience.com/shift-bioscience-raises-16m-to-advance-ai-virtual-cell-platform-for-cell-rejuvenation/),
  [N. American facilities](https://www.businesswire.com/news/home/20250218045176/en/Shift-Bioscience-Establishes-North-American-Facilities-to-Expand-Capabilities-of-AI-Powered-Virtual-Cell-Technology)

**Caveat — treat the identity as a strong inference, not a fact.** No public write-up ties
`cellshift.bio` to Shift Bioscience by name, and no cellshift Track B method is disclosed
anywhere we could find. What is load-bearing is the *class*: whoever they are, a team that
tops the **tool-use** track by a wide margin, under a name that reads as "cell / shift /
perturbation," is far more likely a **perturbation-data company wiring its data/model in as a
tool** than a string-ML notebook. The competitor-landscape page already flagged exactly this
suspicion ([[competitor-landscape]] — "the *true* leaders use real external-knowledge tools").

## What could a tool-based agent do that we did NOT — ranked by 4-day expected value

We already fired the obvious agentic lever: a per-row **LLM agent over retrieved GO/STRING**,
calibrated (0% abstention) — it landed at DE **parity** (0.578, CI [0.549, 0.607]), not a
break ([[external-knowledge-does-not-crack-de]]). So "give the LLM external knowledge" is
spent. The untried space, ranked:

### 1. Proprietary / company-scale perturb-seq atlas as a queried tool — HIGH plausibility for 0.752, but NOT a legal/available lever for us

The one thing that can beat our DE wall is **not "transfer" — it is direct measured labels**
for the actual test perturbations in the actual cell context. Our DE-unlearnable result is
precise: no *transferable* signal from *public/small/OOD* sources
([[de-unlearnable-on-dual-ood]], [[direction-transfers-de-doesnt]]). A company atlas that
directly measured the challenge's (pert, gene) pairs in the matching cell type would be a
**lookup, not a transfer**, and would sail past the 0.555 oracle ceiling (which bounds only
identity/marginal channels, not ground-truth measurement).

- **(a) Plausibility it explains 0.752: high.** It is the only mechanism in evidence that can
  add real DE signal, and it fits cellshift's profile exactly (a perturb-seq data company).
- **(b) Rules-legal? No — for us, and questionable for anyone.** `docs/kaggle-rules.md` Track B
  lists allowed data augmentation as **PerturbQA + Tahoe-100M only** (permissively licensed);
  proprietary data is not on that list. A rules-compliant entrant *cannot* use a private atlas
  either — so if cellshift did, it is arguably non-compliant; if they did not, this lever
  doesn't explain them. Either way it is **closed to us**.
- **(c) Can we try it in 4 days? No.** We have no proprietary atlas, and the public atlases
  we *could* reach are (i) largely off the allowed-data list and (ii) already measured null:
  **PerturbQA** human-ortholog transfer collapsed to Δ+0.001 on the real board;
  **native-mouse Traxler KO150** gave Δ−0.005; and **82/96 test perturbations are
  essential-housekeeping genes never screened in any borrowable macrophage dataset** →
  coverage ≈0 by construction ([[de-unlearnable-on-dual-ood]], [[direction-transfers-de-doesnt]]).
  The real-LB read confirmed our split is **honest**, not over-hard — so a bigger public atlas
  hits the same coverage + context walls.

**Read: this is the most-likely story for 0.752, and it is a data moat, not a lever.**

### 2. TabPFN / tabular FM as the PRIMARY predictor over rich functional features — LOW plausibility for 0.752, but the top *legal + untried* option

The competitor-landscape open lane. TabPFN as a **combiner** over our 3 saturated DIR channels
is already dead (0.613 < 0.651 neighbour-DIR; [[tabpfn-for-perturbation-tracks]]). Framing #2 —
TabPFN as the **primary predictor** over rich pair features (pert GO/pathway/embedding × gene
expr/centrality) — is **genuinely untried by us**.

- **(a) Plausibility it explains 0.752: low.** Palla et al. show tabular FMs are SOTA for
  perturbation prediction *but only modestly positive in the hardest genome-wide OOD-both-axes
  setting* (+0.108 cosine). On our axes it cannot manufacture DE signal the oracle already
  ceilinged at 0.555, and on direction it is unlikely to beat neighbour-DIR's 0.651. Expect a
  cheap strong baseline (~0.585–0.60 mean), not a 0.75 cracker.
- **(b) Rules-legal? Yes (best reading).** A frozen, in-context tabular FM is neither the fixed
  base LLM, a fine-tune of it, nor an external *LLM* — it is a local tool, and tools are allowed
  (≤100). Confirm on the JS-rendered Rules tab before relying on it (`docs/kaggle-rules.md`).
- **(c) Can we try it in 4 days? Yes, cheaply** — one Track A featurize→classify run on
  `doubly_disjoint_folds`; it doubles as the Track B anchor tool.

**Read: the single highest-EV *legal* bet, but its EV is a floor-raiser (+0.00–0.02), not a
rank chase.**

### 3. Smarter direction modeling than 0.65 — NIL plausibility for 0.752

Closed hard: equal-weight (0.642), weighted (0.660, within σ), and a learned stacker (0.641)
all fail to robustly beat neighbour-DIR alone (0.651); co-essentiality is a *weaker* key than
STRING ([[dir-ceiling-equal-weight-fusion]], [[external-knowledge-does-not-crack-de]]). Even a
perfect ~0.70 DIR with DE pinned ~0.55 caps the mean near ~0.625 — arithmetically it cannot
reach 0.752. Not the explanation; not worth a shot.

### 4. Structural / test-set / calibration / ensembling tricks — NIL–LOW plausibility, exhausted

Transductive tricks (train+test-union vocab, id-in-text) measured ≈0.000 on OOD and are
mechanically inert on an exact-identity-OOD test ([[field-gap-586-693]]). Calibration is
already done (0% abstention); ensembling weak channels drags ([[dir-ceiling-equal-weight-fusion]]).
No legal structural lever remains untried with meaningful EV.

## The honest arithmetic on 0.752

Our honest mean ceiling is ~0.60 (DIR ~0.65 + DE pinned ~0.55). Track A's public top 0.693
**already doesn't reproduce** — a faithful char-ngram two-stage reaches only real-LB 0.552, and
the +0.10 residual is undisclosed engineering or inflation ([[field-gap-586-693]]). Track B's
0.752 is **higher still, on the harder agentic track**. Two non-exclusive explanations survive:

1. **Data moat (most likely):** a perturbation-data company using proprietary/company-scale
   perturb-seq — possibly in the matching mouse-macrophage context — as an agent tool, turning
   DE from a transfer problem (unlearnable, our wall) into a lookup (learnable, past the oracle).
   Fits cellshift's identity; **not replicable or rules-available to us.**
2. **Inflation / undisclosed engineering (plausible contributor):** the same phenomenon that
   makes 0.693 unreproducible could inflate 0.752 on the public LB. Unfalsifiable from outside
   without their notebook, but consistent with the field-gap finding.

Both point the same way for us: **no rules-legal, still-available lever gets us near 0.752.**

## Verdict

- **Is 0.752 a replicable lever or proprietary data?** Most plausibly **proprietary data used
  as a tool** (a data moat) — reinforced by cellshift.bio ≈ Shift Bioscience, a perturb-seq
  company — with a likely dose of public-LB inflation. **Not a method we are failing to copy.**
- **Is there a concrete rules-legal lever worth a final 4-day sprint?** The only legal + untried
  option is **TabPFN-as-primary-predictor** (framing #2), and its honest EV is a **floor-raiser
  (~+0.00–0.02 mean, landing ~0.585–0.60)**, not a path to 0.752. Given the DE-unlearnable
  capstone (oracle 0.555, format-independent) and the real-LB-confirmed honest split, **0.752 is
  honestly out of reach** for any lever legal-and-available to us before the deadline.
- **Recommendation:** **do not sprint to chase 0.752.** Bank the honest ceiling (the project's
  publishable negative result, [[de-unlearnable-on-dual-ood]]). If any final effort is spent, run
  TabPFN-primary-predictor as a cheap Track A/B floor-raiser and read it as a baseline, not a
  rank bet — and only after confirming tabular-FM legality on the Track B Rules tab.

## To verify (if ever revisited)

- Direct confirmation that `cellshift.bio` = Shift Bioscience (whois / a de-Cloudflared fetch /
  the Kaggle team profile) and any post-deadline method disclosure.
- Whether the Track B Rules tab (JS-rendered) explicitly permits offline/precomputed tabular
  models as tools, and whether proprietary perturbation data is barred beyond the PerturbQA +
  Tahoe-100M allow-list.

## See also

[[competitor-landscape]] (flagged the cellshift 0.752 anomaly + the open lanes) ·
[[external-knowledge-does-not-crack-de]] (agentic external-knowledge = DE parity) ·
[[de-unlearnable-oracle-ceiling]] · [[de-unlearnable-on-dual-ood]] ·
[[direction-transfers-de-doesnt]] · [[dir-ceiling-equal-weight-fusion]] ·
[[field-gap-586-693]] · [[tabpfn-for-perturbation-tracks]]
