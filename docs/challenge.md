# BioReasoning Challenge 2026

Canonical team summary of the BioReasoning Challenge 2026, organized by
Genentech's BRAID team and held at the **MLGenX Workshop @ ICLR 2026**.

This document is the source of truth for what the challenge is, which
track(s) we enter, and how submissions work. Track-level detail (data,
scoring, format) is filled in by subsequent goals on this branch.

## Motivation

The challenge asks whether LLMs and agentic systems can do more than talk
about biology — whether they can serve as useful computational engines for
predicting cellular behavior. Concretely, participants predict
**perturbation outcomes in macrophages**, combining biological knowledge
with structured reasoning to anticipate intervention effects.

## Tracks

Three tracks, each fixing a different axis of the LLM-engineering design
space so contributions are comparable.

- **Track A — Prompt-only (no tools, single call).** Optimize prompting
  with a fixed LLM. No fine-tuning, no tool use, single forward call.
- **Track B — (Multi-)agentic tool-use.** Design tools and multi-agent
  architectures around a fixed LLM. No fine-tuning of the base model.
- **Track C — Fine-tuning (reasoning, no tools).** Fine-tune an open model
  under 10B parameters using any fine-tuning technique. No tool use.

Deeper per-track sections (data, evaluation, constraints) are appended in
later goals on the `docs/scope-tracks` branch.

## Timeline

Not published on the overview page as of 2026-06-06. Expected to be
documented on the Kaggle competition pages — see Goals 2–3.

## Eligibility

The overview page states the challenge "will follow a good-faith policy
regarding cheating" but does not specify team size limits or participant
restrictions. Track-specific constraints (base model, parameter limits,
token budgets) live in the per-track sections. General eligibility to be
confirmed from Kaggle and updated here.

## Organizers

Organized by **Genentech (BRAID team)**. Listed organizers include Carl
Edwards, Ehsan Hajiramezanali, Sara Mostafavi, and Aviv Regev, among
others.

## References

- Challenge overview: https://genentech.github.io/BioReasoningChallenge/
- Track A (Kaggle): https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-a
- Track B (Kaggle): https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-b
- Workshop: MLGenX @ ICLR 2026

_Overview fetched 2026-06-06. Re-check before any decision that depends on
timeline or eligibility._
