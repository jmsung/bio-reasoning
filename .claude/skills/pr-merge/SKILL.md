---
name: pr-merge
description: Post-merge cleanup after a human squash-merges in GitHub. Verify merge, archive mb tracking file, prune worktree, delete local branch.

disable-model-invocation: true
---

Closes the PR loop: optionally squash-merge via CLI if the PR is still
open, sync local `main`, archive the tracking file if present, prune the
worktree if present, and delete the local branch.

Two human-driven merge paths land here:
- **Merged in GitHub UI already** → `/pr-merge` skips the merge step and
  just cleans up.
- **Still open** → `/pr-merge` offers to `gh pr merge --squash` on your
  confirmation, then cleans up.

Two repo-layout shapes are supported automatically:
- **Linked worktree** (universal layout: `<umbrella>/cb/` main checkout,
  `<umbrella>/cb-<slug>/` feature worktree, sibling `<umbrella>/mb/`):
  full flow — archive tracking file, remove the worktree.
- **Plain clone** (`git clone bio-reasoning && cd bio-reasoning`, switch
  branches via `git checkout`): the clone IS the main checkout; step 3
  switches it back to `main` in place; mb-archive and worktree-remove
  steps are skipped silently.

Layout is detected via `$REPO/.git`: a **file** (pointer to
`.git/worktrees/<name>/`) → linked worktree; a **directory** → plain
clone.

Pairs with [`/pr-open`](../pr-open/SKILL.md). See
`knowledge/wiki/decisions/0001-pr-workflow.md`.

## Steps

### 1. Verify state + detect layout

```bash
REPO=$(git rev-parse --show-toplevel) || { echo "Not in a git repo." >&2; exit 1; }
BRANCH=$(git -C "$REPO" branch --show-current)
[ "$BRANCH" = "main" ] && { echo "Run /pr-merge from a feature branch, not main." >&2; exit 1; }
SLUG="${BRANCH//\//-}"

# Layout detection — drives the conditional steps below.
if [ -f "$REPO/.git" ]; then
  LAYOUT=worktree                # linked worktree (.git is a pointer file)
  UMBRELLA="$(dirname "$REPO")"
  BRANCH_FILE="$UMBRELLA/mb/active/$SLUG.md"
elif [ -d "$REPO/.git" ]; then
  LAYOUT=plain                   # main checkout in a regular clone
  UMBRELLA=""                    # no umbrella in plain mode
  BRANCH_FILE=""                 # no tracking file in plain mode
else
  echo "Cannot determine repo layout — $REPO/.git is neither file nor dir." >&2; exit 1
fi
```

Tracking file is required in worktree mode (`/pr-open` would have
refused without it), optional in plain mode. Don't abort here on a
missing tracking file in plain mode — just skip the archive step later.

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
# Locate the cb checkout that has `main` (or will).
if [ "$LAYOUT" = "plain" ]; then
  # Plain clone: this clone IS the main checkout. Switch branches here.
  CB_ROOT="$REPO"
else
  # Linked worktree: find a sibling worktree with main checked out.
  CB_ROOT=$(git -C "$REPO" worktree list --porcelain | \
    awk '/^worktree/{p=$2} /^branch refs\/heads\/main$/{print p; exit}')
  # Fallback to universal layout convention: $REPO is under <umbrella>/cb-<slug>/;
  # main checkout is at <umbrella>/cb/.
  [ -z "$CB_ROOT" ] && CB_ROOT="$UMBRELLA/cb"
fi
[ -d "$CB_ROOT/.git" ] || [ -f "$CB_ROOT/.git" ] || {
  echo "Could not locate the main checkout (tried: $CB_ROOT)." >&2; exit 1
}

git -C "$CB_ROOT" fetch origin
git -C "$CB_ROOT" checkout main
# Brief retry on ff-only failure: GitHub returns from gh pr merge
# before the new commit is fully replicated to the user's remote view.
git -C "$CB_ROOT" pull --ff-only origin main || {
  sleep 2
  git -C "$CB_ROOT" pull --ff-only origin main
} || {
  echo "pull --ff-only failed twice — main has diverged unexpectedly." >&2
  echo "Resolve manually; do NOT force." >&2
  exit 1
}
```

### 4. Archive the tracking file (worktree mode only)

```bash
if [ "$LAYOUT" = "worktree" ] && [ -f "$BRANCH_FILE" ] \
   && ( [ -d "$UMBRELLA/.git" ] || [ -f "$UMBRELLA/.git" ] ); then
  mkdir -p "$UMBRELLA/mb/completed"
  git -C "$UMBRELLA" mv "mb/active/$SLUG.md" "mb/completed/$SLUG.md"
  PR_NUM=$(gh pr view --json number -q .number)
  git -C "$UMBRELLA" commit -m "mb($SLUG): archive — PR #$PR_NUM merged"
else
  echo "Plain clone or no tracking file — skipping mb archive."
fi
```

Plain clones have no `mb/` to archive; we skip silently.

### 5. Prune the worktree (worktree mode only; CWD-critical)

In **plain mode**, skip — step 3 already switched the clone to `main`,
no worktree to remove. The teammate's checkout stays put.

In **worktree mode**, removal is delicate. The Bash tool's CWD
persists between calls. If CWD is inside the worktree when
`git worktree remove` deletes it, every subsequent Bash call fails
with "Path does not exist" — no recovery within the session. So either
(a) chain `cd "$CB_ROOT"` with the remove in a SINGLE shell invocation
(both run before the harness can reset CWD), or (b) cd standalone first.
Pattern (a) is the simpler, robust default:

```bash
if [ "$LAYOUT" = "worktree" ]; then
  cd "$CB_ROOT" && git worktree remove "$REPO"
fi
```

If the worktree has uncommitted changes (shouldn't, post-merge),
`git worktree remove` exits non-zero — surface and stop, let the user
resolve. Do NOT verify removal with `git worktree list` afterward —
that's another Bash call from a potentially-just-reset CWD; trust the
remove's exit code.

### 6. Delete the local branch

```bash
git -C "$CB_ROOT" branch -d "$BRANCH"
```

If `-d` refuses ("not fully merged" — happens when the squash hash
differs from the local branch tip), retry with `-D` only after
confirming the PR was merged in step 2.

The remote branch is auto-deleted by GitHub (`delete_branch_on_merge: true`).

### 7. Report

Worktree mode:
```
PR #<N> merged: <URL>
Layout:       worktree
Branch:       <branch> — deleted locally
Worktree:     <path> — pruned
Tracking:     mb/active/<slug>.md → mb/completed/<slug>.md
Next:         /worktree-start <type>/<slug> to begin the next branch.
```

Plain-clone mode:
```
PR #<N> merged: <URL>
Layout:       plain clone
Branch:       <branch> — deleted locally
Checkout:     <path> — switched to main
Next:         git checkout -b <type>/<slug> to begin the next branch.
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
- `pull --ff-only origin main` fails twice (after the retry).
- Worktree mode and the worktree has uncommitted changes.
- `git branch -d` refuses *and* PR state is not clearly `MERGED`.
- Layout detection fails (`$REPO/.git` is neither file nor directory).

## Idempotency

Safe to re-run if a step fails partway through — each step is a
no-op if the prior state is already correct (branch already deleted,
file already moved, etc.). Errors from "already done" are silently
swallowed.
