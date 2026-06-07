---
name: commit
description: Commit the current goal locally after verifying checks and gcm block. Never pushes.

disable-model-invocation: true
---

Commit the current goal **locally only**. Runs project checks, finds the
right gcm block, stages relevant files, commits. Pairs with
[`/goal`](../goal/SKILL.md) and [`/act`](../act/SKILL.md) — those
are personal harness skills, but the conventions they leave in
`mb/active/<slug>.md` are honored here too if they exist.

**Never pushes.** Push happens via [`/pr-open`](../pr-open/SKILL.md).

## Steps

### 1. Verify state

```bash
REPO=$(git rev-parse --show-toplevel) || { echo "Not in a git repo." >&2; exit 1; }
BRANCH=$(git -C "$REPO" branch --show-current)
[ "$BRANCH" = "main" ] && { echo "Refuse to /commit directly to main — open a branch." >&2; exit 1; }
```

### 2. Run project checks

```bash
uv run pre-commit run --all-files     # full hook sweep
uv run pytest -q                       # tests
uv run mypy                            # type check
```

If any check fails, print the failure verbatim and stop. Do not commit
broken code. (The pre-commit hook will fire again on the actual
`git commit`, but running here surfaces failures before staging.)

### 3. Find the gcm block (optional — for teammates using mb tracking)

If `mb/active/<slug>.md` exists (where `slug = $BRANCH` with `/` → `-`):

1. Read the file.
2. Find the **current goal** — first goal in the `# Goals` section with
   any pending `[ ]` sub-tasks, OR the goal whose sub-tasks just turned
   all `[x]`.
3. Verify ALL sub-tasks for that goal are `[x]`. If any remain,
   abort: "Goal N has pending sub-tasks — finish them or `/revise`."
4. Extract the `gcm "..."` block immediately below that goal's progress
   section. That's the commit message.

If no `mb/active/<slug>.md` exists (teammates without universal layout):

- Ask the user: "No tracking file. Enter a commit message [type(scope): description]:"
- Use what they provide.

### 4. Stage relevant files

```bash
git -C "$REPO" status -s
git -C "$REPO" diff --stat
```

Stage by specific paths (NEVER `-A`):

```bash
git -C "$REPO" add <files matching the goal's scope>
```

If unsure which files belong to the goal, ask. Don't stage everything.

### 5. Commit

```bash
git -C "$REPO" commit -m "$(cat <<'EOF'
<gcm message body from step 3>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

The pre-commit hook fires here — if it modifies files (e.g.,
end-of-file-fixer), the commit aborts. Re-stage the modified files and
re-commit. Never `--no-verify`.

### 6. MB companion commit (only if umbrella layout)

If the umbrella git exists (`$REPO`'s parent directory has its own `.git`):

```bash
UMBRELLA="$(dirname "$REPO")"
if [ -d "$UMBRELLA/.git" ] || [ -f "$UMBRELLA/.git" ]; then
  MB_CHANGES=$(git -C "$UMBRELLA" status --porcelain mb/)
  if [ -n "$MB_CHANGES" ]; then
    git -C "$UMBRELLA" add mb/
    git -C "$UMBRELLA" diff --cached --stat
    # Commit message: same type/scope as cb commit but describing mb changes.
    git -C "$UMBRELLA" commit -m "<derived from step 5's message>"
  fi
fi
```

Skip silently if no umbrella or no mb changes.

### 7. Report

```
Committed <hash> on <branch>
Files: <N changed>

mb companion: <hash> | none
```

If all goals in the tracking file are now `[x]`, nudge:
"All goals complete. Run `/pr-open` to push + open PR."

## What this skill does NOT do

- **Does not push.** Push happens via `/pr-open`.
- **Does not skip hooks.** Pre-commit fires on every commit.
- **Does not stage everything (`-A`).** Specific paths only.
- **Does not amend.** A failed commit → fix and re-commit, never amend.

## Pause heuristics

Stop and surface to the user when:
- Any project check (pre-commit / pytest / mypy) fails.
- The tracking file's current goal has pending sub-tasks.
- The pre-commit hook on `git commit` modifies files (re-stage + re-commit, but tell the user what changed).
- File staging is ambiguous (multiple goals' work in the worktree).
