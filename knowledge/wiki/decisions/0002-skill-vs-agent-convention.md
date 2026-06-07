---
title: When to use skill form vs agent form
date: 2026-06-06
status: accepted
cites:
  - 0001-pr-workflow.md
---

# 0002 — Skill form vs agent form

**Status:** accepted. Codifies the implicit convention already in use
across Jongmin's harness (30 skills, 5 agents). Applies globally to all
projects that share the harness.

## Decision

```
Default: skill form.
Exception: parallel-reviewer subagents called by a quality-gate
           orchestrator skill.
```

That's the whole rule. Two sub-rules follow from it:

1. **Anything user-facing → skill.** Lifecycle (`/goal`, `/act`,
   `/commit`, `/worktree-start`, …), research (`/wiki-query`,
   `/wiki-ingest`, …), config (`/dev-setup`, `/sync-references`, …),
   convenience (`/where`, `/copy-clipboard`, …) — all skills.
2. **Multiple independent reports needed in parallel → agents.**
   When N reviewers must each look at the same thing without conflict
   and return a verdict, each is an `@agent`. The orchestrator that
   spawns them is still a skill with `disable-model-invocation: true`.

## Why

| Property | Skill | Agent |
|---|---|---|
| Runs in parent's context | yes | no — isolated |
| Sequential vs parallel | sequential | parallel |
| Can pause for `[y/n/edit]` | yes | no |
| Returns | drives the conversation | one final report |
| Token cost | adds to your context | own context, condensed return |

Most work in this harness is user-facing or interactive — skills win on
those dimensions. The exception is quality gates: 4 reviewers running
sequentially is ~3× slower than 4 in parallel, and the live-conversation
ability of skills is wasted when you want a bulk verdict.

## Evidence — the survey

Inventory snapshot (2026-06-06):

- **30 skills.** Categories: lifecycle (10), research/synthesis (8),
  git ops (3), config/setup (4), convenience/meta (4), quality-gate
  orchestrator (1 — `/review-pr`).
- **5 agents.** All match the "isolated parallel reviewer" shape:
  - `@security-audit` — HARD gate
  - `@code-review` — soft gate
  - `@docs-review` — auto-fixes
  - `@distill` — extracts to `mb/`
  - `@researcher` — one-off background context (anomaly — currently
    unreferenced by any skill; see Open questions)

Two orchestrator skills spawn agents in parallel:

- `/worktree-done` spawns 4 (`@security-audit`, `@code-review`,
  `@docs-review`, `@distill`)
- `/review-pr` spawns 3 (`@security-audit`, `@code-review`,
  `@docs-review`)

**Zero exceptions** in the existing harness. The rule was implicit
before this doc; it just hadn't been written down.

## Practical guide

**When you're adding new harness functionality, ask in order:**

1. Is the user invoking this directly with `/<name>`? → skill.
2. Will it pause for user input mid-run? → skill.
3. Is it one of several independent inspectors all running on the same
   input simultaneously? → agent (and write the orchestrator skill
   that spawns it alongside).
4. Otherwise → skill.

**Both-forms case:** if you're tempted to make the same thing both a
skill and an agent (e.g., `code-review` exists as both in some harnesses),
don't. Pick one. The agent form is more flexible (a skill can wrap an
agent trivially; an agent wrapping a skill is awkward).

## Application — `/pr-open` quality gate

The team-shared `/pr-open` skill (this project) should follow this rule:
spawn 4 agents in parallel — `@code-review`, `@security-audit`,
`@docs-review`, `@wiki-lint` — not the current mix of `/code-review`
skill + agents + `/wiki-lint` skill.

Implementation cost: write `~/.claude/agents/wiki-lint.md` (thin wrapper
around the lint logic). Then switch `/pr-open`'s gate to all-agents.
Tracked separately — not done in this decision record.

## Open questions

- **`@researcher` is unreferenced.** No skill spawns it; it's only
  invoked ad-hoc. Either delete it (dead code), reference it from
  `/wiki-research` or `/deep-research`, or leave it as an
  invoke-by-name agent for explicit ad-hoc use. Pick one.
- **`/review-pr` (harness) vs `/pr-open` (this project) overlap.**
  Both are quality-gate orchestrators. Worth understanding before they
  diverge further. (See [[0001-pr-workflow]] for the project flow.)

## Consequences

- Future skill/agent additions follow this rule with no per-decision
  debate.
- Any mixed `/foo` + `@foo` duplicates surfaced in a future audit are
  flagged for consolidation.
- The team-shared `/pr-open` will eventually be conformed (write
  `@wiki-lint` agent, drop `/code-review` skill call, use `@code-review`
  agent). Not blocking — current mix works, just not idiomatic.
