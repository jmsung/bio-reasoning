---
title: Personal vs team skill/agent layering
date: 2026-06-06
status: accepted (spec); implementation deferred
cites:
  - decisions/0002-skill-vs-agent-convention.md
---

# 0003 — Personal vs team skill/agent layering

**Status:** spec accepted; implementation lands in follow-up branches
(`feat/sync-team-skills-bidirectional` on harness, and a one-shot
migration to add `audience:` frontmatter to existing skills).

## Decision

Every skill and agent declares its **audience** in frontmatter. The
sync tool reads that field to decide what's published to team projects,
what's back-synced from projects to harness, and what stays personal.

```yaml
---
name: <skill-or-agent-name>
description: ...
audience: personal | team | both
# (other existing frontmatter)
---
```

| Value | Meaning | Lives in |
|---|---|---|
| `personal` | Single-user, harness-only. Never published. | `~/.claude/skills/<name>/SKILL.md` or `~/.claude/agents/<name>.md` |
| `team` | Team-shared. Source of truth is the project version. | Project `.claude/...`. May ALSO live in harness as a published-back copy. |
| `both` | Same body works for personal and team use. Source of truth is harness. | Harness, with auto-publish to project `.claude/...` on sync. |

**Default for files without `audience:`** → `personal` (conservative —
never accidentally publish).

## Rules

### 1. Single file by default

Most skills and agents are one file with one `audience` declaration:

- A personal-only convenience? → `audience: personal`, lives only in harness.
- An identical body for both personal and team use? → `audience: both`,
  lives in harness, gets published to projects.

### 2. Twin files when bodies genuinely diverge

When the personal and team versions need substantively different bodies
(e.g., personal uses harness paths and `proj_root_init`; team is graceful
degrade), keep two files:

```
~/.claude/skills/commit/SKILL.md         audience: personal
~/.claude/skills/commit/SKILL-team.md    audience: team
Project .claude/skills/commit/SKILL.md   audience: team    ← synced from harness's -team.md
```

Both files carry their own `audience:` declaration. The suffix `-team.md`
is the explicit hint that a divergent team variant exists alongside the
personal one.

### 3. Sync mechanics

**Forward sync** (harness → project): `/sync-team-skills`. Walks harness,
publishes everything marked `audience: team` (from `-team.md` twin files)
or `audience: both` (from canonical files) into the project's
`.claude/skills/` and `.claude/agents/`.

**Back-sync** (project → harness): a new path, either
`/sync-team-skills --back` or `/publish-skills`. For each file in the
project's `.claude/` marked `audience: team` or `both`:

1. Find the matching file in harness — `-team.md` twin if it exists,
   else the canonical `SKILL.md`.
2. Diff. If identical, skip.
3. If different, prompt the user: show the diff, ask y/n to update
   harness as the new source of truth.

The back-sync is the mechanism that prevents drift: any team variant
polished during a real-PR session (as happened to `/pr-open` and
`/pr-merge` on `docs/team-scaffold`) flows back into harness, so
future `/sync-team-skills` calls from other projects pull the latest.

## Why

### Problem this solves

Today's pattern (pre-0003):
- Some skills exist in both harness AND project, copied by hand.
- Drift is silent: a polish to the project version doesn't reach harness;
  a polish to harness doesn't reach projects unless `/sync-team-skills`
  is run.
- Agents have no team-sharing convention at all — they're copied
  ad-hoc when projects need them.

Post-0003:
- Frontmatter declares intent explicitly. `grep '^audience: team'`
  lists what's shareable.
- Sync is bidirectional. Source of truth is clear per audience value.
- Agents and skills follow the same pattern.

### Why frontmatter beats pure suffix convention

The existing `SKILL.md` vs `SKILL-team.md` convention requires
duplication even when the team version is identical to the personal
one (as it is for `@code-review`, `@security-audit`, `@docs-review` —
we literally copied them verbatim in this branch).

Frontmatter collapses the identical-body case to one file with
`audience: both`. The suffix convention only kicks in for genuine
divergence.

## Application to existing inventory

### Harness (`~/.claude/skills/`, `~/.claude/agents/`)

After migration, every file gets an `audience:` line:

| Item | audience | Notes |
|---|---|---|
| `/goal`, `/act`, `/where`, `/revise` | `personal` | Assume harness layout and `proj_root_init`. |
| `/worktree-start`, `/worktree-done` | `personal` | Per-user worktree mechanics + accounting. |
| `/project-start`, `/project-done`, `/project-archive` | `personal` | Per-user portfolio management. |
| `/wiki-{query,ingest,learn,lint,audit,plan,research,edit}` | `both` (probably) | Bodies don't depend on personal paths; verify per file during migration. |
| `/git-sync`, `/git-sync-proj`, `/git-sync-all` | `both` (single-repo variant) and `personal` (workspace-wide variants) | Per-project sync works for teams; workspace-wide doesn't. |
| `/sync-team-skills`, `/sync-references` | `personal` | They mutate harness or workspace state. |
| `/copy-clipboard`, `/queue`, `/run-branch` | `personal` | Personal-flow orchestration. |
| `@code-review`, `@security-audit`, `@docs-review`, `@wiki-lint` | `both` | Identical bodies; ship as-is to teams. |
| `@distill`, `@researcher` | `personal` (distill), TBD (researcher) | Distill writes to per-user mb. Researcher's status is open per 0002. |
| `/commit` | twin: `SKILL.md` (personal) + `SKILL-team.md` (team) | Bodies legitimately diverge. |

### This project (`.claude/skills/`, `.claude/agents/` on `docs/team-scaffold`)

Everything in `.claude/` should declare `audience: team` after migration:

- `/dev-setup` SKILL.md → `audience: team`
- `/pr-open` SKILL.md → `audience: team`
- `/pr-merge` SKILL.md → `audience: team`
- `/commit` SKILL.md → `audience: team` (was the team variant)
- `/wiki-{ingest,query,learn,lint}` SKILL.md → `audience: team`
- `/git-sync` SKILL.md → `audience: team`
- `@code-review`, `@security-audit`, `@docs-review`, `@wiki-lint` → `audience: team`

These project files are the **source of truth** for the team variants
from this point on. The first back-sync writes them into harness
(creating `-team.md` twins for the divergent ones, or canonical files
with `audience: both` for the identical ones).

## Consequences

- Implementing this requires: (a) a one-shot migration to add
  `audience:` to every existing harness skill/agent (~35 files);
  (b) extending `/sync-team-skills` to read the field and to support
  `--back`; (c) optionally a sanity-check lint that flags files
  without `audience:` set.
- The convention is opt-in to migrate but enforced on new skills going
  forward. Lint can flag missing `audience:` as a warning.
- See [[0002-skill-vs-agent-convention]] for the agent vs skill choice
  itself (orthogonal to audience).

## Open questions

- **Naming of the back-sync entry point.** `/sync-team-skills --back`
  (one skill, two directions) vs `/publish-skills` (separate skill).
  Lean: flag, because the discovery and matching logic is shared.
- **Agent body lint.** Should `@wiki-lint`-style agents declare what
  they write to? Out of scope for 0003 but worth a follow-up.
- **`@researcher` is still unreferenced** (carried over from 0002).
  When 0003 ships, `@researcher` needs an `audience:` — `personal`
  pending the unreferenced-status resolution.

## Implementation plan (sketch)

1. **Harness branch `feat/sync-team-skills-bidirectional`:**
   - Extend `/sync-team-skills` to read `audience:` and to support
     forward + back-sync.
   - Add a `--back` flag (or new skill) implementing the diff-prompt-update flow.
   - One-shot migration script: walk every harness skill/agent, add
     `audience:` line. Default `personal`; override per the table above.
2. **This project's first back-sync** (after the harness branch lands):
   run `/sync-team-skills --back` from `cb-docs-team-scaffold/` to flow
   `/pr-open`, `/pr-merge`, `/dev-setup`, `/commit` (team variant),
   `@wiki-lint`, etc. into harness. Verify the diff and accept.
3. **Lint addition:** `/wiki-lint` (or a new `harness-lint`) flags any
   skill/agent file without `audience:` as a warning.
