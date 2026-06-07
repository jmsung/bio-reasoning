---
name: pr-merge
description: Post-merge cleanup after a human squash-merges in GitHub. Verify merge, archive mb tracking file, prune worktree, delete local branch.

disable-model-invocation: true
---

Closes the PR loop: optionally squash-merge via CLI if the PR is still
open, then sync local `main`, archive the `mb/active/<slug>.md` tracking
file to `mb/completed/`, prune the worktree, and delete the local
branch.

Two human-driven merge paths land here:
- **Merged in GitHub UI already** → `/pr-merge` skips the merge step and
  just cleans up.
- **Still open** → `/pr-merge` offers to `gh pr merge --squash` on your
  confirmation, then cleans up.

Pairs with [`/pr-open`](../pr-open/SKILL.md). See
`knowledge/wiki/decisions/0001-pr-workflow.md`.

## Steps

### 1. Verify state

```bash
REPO=$(git rev-parse --show-toplevel) || { echo "Not in a git repo." >&2; exit 1; }
BRANCH=$(git -C "$REPO" branch --show-current)
[ "$BRANCH" = "main" ] && { echo "Run /pr-merge from the feature branch's worktree, not main." >&2; exit 1; }
```

Derive `SLUG="${BRANCH//\//-}"` and locate `mb/active/$SLUG.md` (under
the umbrella, not the cb worktree). Abort if missing.

### 2. Check PR state — auto-merge if open

```bash
STATE=$(gh pr view --json state -q .state 2>/dev/null) || {
  echo "No PR found for $BRANCH — did /pr-open run?" >&2; exit 1
}
case "$STATE" in
  MERGED)
    # Already merged in the GitHub UI — skip the merge step.
    ;;
  OPEN)
    # Ask the human to confirm before mutating main.
    echo "PR #$(gh pr view --json number -q .number) is OPEN."
    echo "Squash-merge now via CLI? [y/N]"
    read REPLY
    case "$REPLY" in
      y|Y)
        # No --delete-branch — we own branch + worktree cleanup below,
        # and --delete-branch fails on worktrees by trying to switch.
        gh pr merge --squash || {
          echo "gh pr merge failed — aborting." >&2; exit 1
        }
        ;;
      *)
        echo "Aborting. Either merge in the GitHub UI and re-run, or rerun and answer 'y'." >&2
        exit 1
        ;;
    esac
    ;;
  CLOSED)
    echo "PR was closed without merging — aborting." >&2; exit 1
    ;;
  *)
    echo "Unexpected PR state: $STATE" >&2; exit 1
    ;;
esac
```

Mandatory human gate: the skill never merges without explicit `y`.

### 3. Fetch + checkout main

```bash
# Switch to main inside the umbrella's cb checkout (NOT the worktree).
CB_ROOT=$(git -C "$REPO" worktree list --porcelain | awk '/^worktree/{print $2; exit}')
git -C "$CB_ROOT" fetch origin
git -C "$CB_ROOT" checkout main
git -C "$CB_ROOT" pull --ff-only origin main
```

If `pull --ff-only` fails (main has diverged unexpectedly), surface and
stop — do not force.

### 4. Archive the tracking file

```bash
UMBRELLA=$(git -C "$REPO" rev-parse --show-toplevel | xargs dirname)
mkdir -p "$UMBRELLA/mb/completed"
git -C "$UMBRELLA/mb" mv "active/$SLUG.md" "completed/$SLUG.md"
git -C "$UMBRELLA/mb" commit -m "mb($SLUG): archive — PR #$(gh pr view --json number -q .number) merged"
```

### 5. Prune the worktree

```bash
WORKTREE=$(git -C "$REPO" rev-parse --show-toplevel)
cd "$CB_ROOT"           # leave the worktree first or `worktree remove` refuses
git worktree remove "$WORKTREE"
```

If the worktree has uncommitted changes (shouldn't, post-merge), abort
and let the user resolve.

### 6. Delete the local branch

```bash
git -C "$CB_ROOT" branch -d "$BRANCH"
```

If `-d` refuses ("not fully merged" — happens when the squash hash
differs from the local branch tip), retry with `-D` only after
confirming the PR was merged in step 2.

The remote branch is auto-deleted by GitHub (`delete_branch_on_merge: true`).

### 7. Report

```
PR #<N> merged: <URL>
Branch:       <branch> — deleted locally
Worktree:     <path> — pruned
Tracking:     mb/active/<slug>.md → mb/completed/<slug>.md
Next:         /worktree-start <type>/<slug> to begin the next branch.
```

## What this skill does NOT do

- **Does not auto-merge silently.** Step 2 may run `gh pr merge --squash` only after an explicit `y` from the user. On `n`, or when the PR is already `MERGED`, the merge step is skipped.
- **Does not force-delete the branch** without confirming PR state first.
- **Does not push.** Remote branch deletion is handled by `delete_branch_on_merge`.
- **Does not modify `main` history.** Only fast-forward pull.

## Pause heuristics

Stop and surface to the user when:
- No PR exists for the branch (probably `/pr-open` was never run).
- PR state is `OPEN` and user answers `n` to the auto-merge prompt, or `CLOSED` (deliberate abandon — `/pr-merge` is the wrong tool).
- `pull --ff-only origin main` fails.
- Worktree has uncommitted changes.
- `git branch -d` refuses *and* PR state is not clearly `MERGED`.

## Idempotency

Safe to re-run if a step fails partway through — each step is a
no-op if the prior state is already correct (branch already deleted,
file already moved, etc.). Errors from "already done" are silently
swallowed.
