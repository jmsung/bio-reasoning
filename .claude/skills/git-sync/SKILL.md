---
name: git-sync
description: Safe-sync this repo — commit pending work, rebase onto origin target, push. Never force-pushes shared/target branches.

argument-hint: [target-branch]
---

Safely sync the current repo against its origin target (usually `main`):
commit pending work, fetch, rebase, push. Never plain `--force`; only
`--force-with-lease` on personal feature branches after a rebase.

For a PR-based workflow on a feature branch, this is the one-shot "catch
up with `main` and push" command.

## Steps

1. **Detect repo state**:
   ```bash
   REPO=$(git rev-parse --show-toplevel) || { echo "Not in a git repo."; exit 1; }
   BRANCH=$(git -C "$REPO" branch --show-current)
   REMOTE=$(git -C "$REPO" remote | head -1)
   [ -z "$REMOTE" ] && { echo "No remote — nothing to sync."; exit 0; }

   # Target priority: explicit arg → open-PR base → main
   if [ -n "$1" ]; then
     TARGET="$1"
   elif gh pr view --json baseRefName -q .baseRefName 2>/dev/null; then
     TARGET=$(gh pr view --json baseRefName -q .baseRefName)
   else
     TARGET=main
   fi
   ON_TARGET=false
   [ "$BRANCH" = "$TARGET" ] && ON_TARGET=true
   ```
   Report the resolved target before proceeding.

2. **Commit pending work** if the tree is dirty:
   - Refuse to auto-commit if any staged/unstaged file looks sensitive
     (`.env`, credentials, secrets, large binaries) — stop and surface.
   - Otherwise, write a Conventional Commit (`type(scope): subject` +
     meaningful body) grouping the changes into one coherent unit.
   - **Never use `--no-verify`.** If a pre-commit hook fails, fix the
     underlying issue and recommit.

3. **Fetch + rebase onto target**:
   ```bash
   git fetch "$REMOTE" "$TARGET"
   ```
   - **On target branch:** `git pull --rebase "$REMOTE" "$TARGET"`.
   - **On feature branch:**
     ```bash
     BEHIND=$(git rev-list --count "HEAD..$REMOTE/$TARGET")
     [ "$BEHIND" -gt 0 ] && git rebase "$REMOTE/$TARGET"
     ```

   **Conflict handling**: stop, list conflicting files with snippets, ask
   per-file. Don't auto-resolve or `--abort` without confirmation.

   **`--ours` / `--theirs` are flipped during rebase.** Git treats the
   branch you're rebasing *onto* as "ours" and the commits being replayed
   as "theirs":
   - `--ours` → keeps the target's version (usually NOT what the user means).
   - `--theirs` → keeps your branch's version.
   - When the user says "keep mine", they almost always mean `--theirs`.
   - Inspect `git diff --staged` before `git rebase --continue`. If the
     resolved content matches the base, the commit will be silently
     dropped — flag this.

4. **Push**:
   - **On target branch:** `git push "$REMOTE" "$BRANCH"`. Never force.
     If rejected, stop and report — don't paper over it.
   - **Feature, no upstream:** `git push -u "$REMOTE" "$BRANCH"`.
   - **Feature, rebase rewrote history (`BEHIND > 0`):**
     `git push --force-with-lease "$REMOTE" "$BRANCH"`.
   - **Feature, otherwise:** `git push "$REMOTE" "$BRANCH"`.
   - **Never plain `--force`** — always `--force-with-lease`, which
     refuses if someone else pushed concurrently.
   - If a PR is open with reviewers / "Changes requested", confirm before
     force-push (it can dismiss reviews).

5. **Report**:
   ```
   Synced <repo> (<branch> → <target>): <hash>, push: <normal|force-with-lease|skipped>
   ```
   If a PR is open, append PR number, URL, and mergeable state.

## Rules

- **Sync against the origin target**, not the branch's tracking ref.
  Target = `main` by default; explicit arg or open-PR base overrides.
- **Commit before sync.** Dirty trees get committed, not stashed —
  sync should leave a clean tree with everything pushed.
- **Never `--no-verify`.** Fix hook failures and recommit.
- **On target branch: never force-push.** Stop and report if push is rejected.
- **On feature branch: only `--force-with-lease`** after a rebase that
  rewrote history. Never plain `--force`.
- **Sensitive files (`.env`, credentials, secrets)**: refuse to auto-commit,
  surface for human decision.
- **Skip silently** if no remote configured.
