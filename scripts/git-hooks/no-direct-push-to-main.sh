#!/usr/bin/env bash
# Refuse direct push to main unless the commits being pushed look like
# PR squash-merges (commit subject ending with "(#NNN)").
#
# Invoked by the pre-commit framework at the pre-push stage. Env vars set
# by pre-commit (see https://pre-commit.com/#pre-commit-during-push):
#
#   PRE_COMMIT_REMOTE_BRANCH — destination branch name (e.g. "main")
#   PRE_COMMIT_FROM_REF      — local sha being pushed
#   PRE_COMMIT_TO_REF        — remote sha at destination (zeros = new branch)
#
# Bypass (don't): `git push --no-verify`.

set -euo pipefail

# Only guard pushes to main; other branches push freely.
[ "${PRE_COMMIT_REMOTE_BRANCH:-}" = "main" ] || exit 0

ZERO="0000000000000000000000000000000000000000"

# Refuse to delete main outright.
if [ "${PRE_COMMIT_FROM_REF:-}" = "$ZERO" ]; then
  echo "ERROR: refusing to delete main." >&2
  exit 1
fi

# First push to main (no prior commit). Allow but warn.
if [ "${PRE_COMMIT_TO_REF:-}" = "$ZERO" ]; then
  echo "warning: first push to main — no prior commit to compare against." >&2
  exit 0
fi

# Inspect each commit being pushed. Refuse if any commit subject doesn't
# end with "(#NNN)" — the GitHub squash-merge marker.
bad=0
while read -r sha; do
  subject=$(git log -1 --pretty=%s "$sha")
  if ! [[ "$subject" =~ \(\#[0-9]+\)$ ]]; then
    echo "  ✗ $sha  $subject" >&2
    bad=1
  fi
done < <(git rev-list "${PRE_COMMIT_TO_REF}..${PRE_COMMIT_FROM_REF}")

if [ "$bad" = 1 ]; then
  cat >&2 <<'EOF'

ERROR: refusing direct push to main.

The commits above don't look like PR squash-merges (no "(#NNN)" suffix).

Use /pr-open to open a PR, then either:
  - squash-merge in the GitHub UI, OR
  - run /pr-merge and answer "y" to gh pr merge --squash.

To override (don't, except for true emergencies): git push --no-verify.
EOF
  exit 1
fi

exit 0
