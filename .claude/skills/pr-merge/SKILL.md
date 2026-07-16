---
name: pr-merge
description: Post-merge cleanup after a human squash-merges in GitHub. Verify merge, archive mb tracking file, prune worktree, delete local branch.

disable-model-invocation: true
---

Closes the PR loop: optionally squash-merge via CLI if the PR is still
open, sync local `main`, verify progress-report freshness (read-only),
archive the tracking file if present, prune the worktree if present, and
delete the local branch.

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
  # .git is a file pointer. Could be a linked worktree OR a submodule;
  # only treat as worktree if it points into a `worktrees/` dir.
  if grep -q '^gitdir: .*/worktrees/' "$REPO/.git"; then
    LAYOUT=worktree
    UMBRELLA="$(dirname "$REPO")"
    BRANCH_FILE="$UMBRELLA/mb/active/$SLUG.md"
  else
    echo "$REPO/.git is a gitfile but not a linked worktree (submodule?)." >&2
    echo "/pr-merge does not support this layout." >&2
    exit 1
  fi
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
  # Refuse to switch branches with uncommitted changes — would lose work.
  if ! git -C "$REPO" diff --quiet || ! git -C "$REPO" diff --cached --quiet; then
    echo "Uncommitted changes on $BRANCH — commit or stash before /pr-merge." >&2
    git -C "$REPO" status --short >&2
    exit 1
  fi
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

### 4. Verify progress-report freshness (conditional; read-only)

If the project keeps `reports/progress-report.md`, sanity-check it against the just-merged
`main` — **read-only**. We do **not** write to `main` here: a post-merge commit would either
diverge local `main` from `origin` (this skill only `pull --ff-only`s, never pushes `main`) or
bypass the "PRs against main, teammate review" gate. The narrative addition and the
`*Last updated:*` stamp are owned by [`/pr-open`](../pr-open/SKILL.md) step 5, on the branch,
where they ride the PR and get reviewed. This step only surfaces drift.

```bash
REPORT="$CB_ROOT/reports/progress-report.md"
if [ -f "$REPORT" ]; then
  # Did the squash-merge commit touch the report? (empty output = it did not.)
  REPORT_TOUCHED=$(git -C "$CB_ROOT" show --stat HEAD -- reports/progress-report.md | grep -c 'progress-report.md')
  # Is the freshness stamp older than today?
  STAMP=$(grep -m1 -oE 'Last updated: [0-9]{4}-[0-9]{2}-[0-9]{2}' "$REPORT" | awk '{print $3}')
  TODAY=$(date +%F)
  # lexical compare is valid for YYYY-MM-DD; [[ ]] required for < on strings
  if [[ -n "$STAMP" && "$STAMP" < "$TODAY" ]]; then
    STALE="stamp $STAMP < $TODAY — consider a follow-up /pr-open"
  else
    STALE=""
  fi
fi
```

Fold `REPORT_TOUCHED` / `STALE` into the final Report (step 8). This never blocks or mutates —
it is purely informational.

### 5. Archive the tracking file (worktree mode only)

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

### 6. Prune the worktree (worktree mode only; CWD-critical)

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

### 7. Delete the local branch

```bash
# We already verified PR state == MERGED in step 2 (or auto-merged it),
# so GitHub is the source of truth. The local branch tip is the
# pre-squash commit — NOT an ancestor of main's squash-merge commit —
# so `git branch -d` would refuse. Use `-D` directly.
git -C "$CB_ROOT" branch -D "$BRANCH"
```

The remote branch is auto-deleted by GitHub (`delete_branch_on_merge: true`).

### 8. Report

Worktree mode:
```
PR #<N> merged: <URL>
Layout:       worktree
Branch:       <branch> — deleted locally
Worktree:     <path> — pruned
Tracking:     mb/active/<slug>.md → mb/completed/<slug>.md
Report:       progress-report updated by this PR ✓ (or "not touched" / "no report") [+ stale-stamp warning if any]
Next:         /worktree-start <type>/<slug> to begin the next branch.
```

Plain-clone mode:
```
PR #<N> merged: <URL>
Layout:       plain clone
Branch:       <branch> — deleted locally
Checkout:     <path> — switched to main
Report:       progress-report updated by this PR ✓ (or "not touched" / "no report") [+ stale-stamp warning if any]
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
- Plain mode and the working tree has uncommitted changes (step 3 guard).
- Layout detection: `$REPO/.git` is a gitfile but doesn't point into `worktrees/` (likely a submodule — unsupported).
- Layout detection: `$REPO/.git` is neither file nor directory.

## Idempotency

Safe to re-run if a step fails partway through — each step is a
no-op if the prior state is already correct (branch already deleted,
file already moved, etc.). Errors from "already done" are silently
swallowed.
