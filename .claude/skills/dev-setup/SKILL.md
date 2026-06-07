---
name: dev-setup
description: One-time teammate onboarding after git clone — uv sync, pre-commit install, verify gh + kaggle auth, check .env.

disable-model-invocation: true
---

Run this **once after `git clone`** (or after pulling changes to
`pyproject.toml` / `.pre-commit-config.yaml`). Sets up the local dev env
so subsequent commits go through pre-commit hooks and `/pr-open` works.

Idempotent — safe to re-run anytime as a "why is my env broken" debug
step.

Pairs with [`/pr-open`](../pr-open/SKILL.md) and
[`/pr-merge`](../pr-merge/SKILL.md). See
`knowledge/wiki/decisions/0001-pr-workflow.md` for the 3-gate model.

## Steps

### 1. Verify uv is installed

```bash
command -v uv >/dev/null || {
  echo "uv not found. Install: https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
}
echo "✓ uv: $(uv --version)"
```

### 2. uv sync

```bash
REPO=$(git rev-parse --show-toplevel) || { echo "Not in a git repo." >&2; exit 1; }
cd "$REPO"
uv sync
echo "✓ uv sync — deps installed"
```

### 3. pre-commit install

```bash
uv run pre-commit install
echo "✓ pre-commit hooks installed (.git/hooks/pre-commit)"
```

Optionally offer a first dry-run sweep so the teammate sees what the
hooks do:

```bash
echo "Run a hook sweep on the whole repo now? [y/N]"
read REPLY
[ "$REPLY" = "y" ] && uv run pre-commit run --all-files
```

### 4. Verify gh auth

```bash
if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
  echo "✓ gh: $(gh api user -q .login) authenticated"
else
  echo "⚠ gh not authenticated — /pr-open will fail. Fix: gh auth login"
fi
```

Warn, do not abort — teammate might not be opening PRs yet.

### 5. Verify kaggle auth

```bash
if command -v kaggle >/dev/null 2>&1 && [ -f "$HOME/.kaggle/kaggle.json" ]; then
  echo "✓ kaggle CLI ready"
else
  echo "⚠ kaggle CLI missing or not configured — data download will fail."
  echo "  Install: uv tool install kaggle"
  echo "  Auth:    download kaggle.json from kaggle.com/settings → ~/.kaggle/kaggle.json"
  echo "  Chmod:   chmod 600 ~/.kaggle/kaggle.json"
fi
```

Warn, do not abort.

### 6. Check .env

```bash
if [ ! -f "$REPO/.env" ]; then
  if [ -f "$REPO/.env.example" ]; then
    echo ".env missing. Copy from .env.example? [y/N]"
    read REPLY
    [ "$REPLY" = "y" ] && cp "$REPO/.env.example" "$REPO/.env" && \
      echo "✓ .env created — edit it to add real API keys"
  else
    echo "⚠ No .env and no .env.example — skipping"
  fi
elif [ -f "$REPO/.env.example" ]; then
  # Diff keys (not values) — surface missing required keys.
  diff <(grep -oE '^[A-Z_]+' "$REPO/.env.example" | sort -u) \
       <(grep -oE '^[A-Z_]+' "$REPO/.env" | sort -u) > /tmp/env-keys-diff || {
    echo "⚠ .env is missing keys from .env.example:"
    grep '^<' /tmp/env-keys-diff | sed 's/^< /  /'
  }
fi
```

### 7. Report

```
Dev env ready.

  uv         ✓
  uv sync    ✓
  pre-commit ✓ (hooks active on next `git commit`)
  gh         ✓ / ⚠
  kaggle     ✓ / ⚠
  .env       ✓ / ⚠ <reason>

Next:
  • Read docs/development.md for the R&D workflow.
  • See docs/roadmap.md for what's open.
  • Start a branch: /worktree-start <type>/<slug>
```

## What this skill does NOT do

- **Does not install `uv`.** Bootstrapping the bootstrapper is a manual step (one-line curl from astral.sh).
- **Does not fix auth.** It reports the gap; teammate runs `gh auth login` etc.
- **Does not edit `.env` values.** Only creates the file from `.env.example` template; secrets are the teammate's job.
- **Does not commit anything.** All changes are to the teammate's local env, not the repo.

## Pause heuristics

Stop and surface to the user when:
- `uv` is not installed (step 1 — hard fail).
- `uv sync` fails (network, lock conflict).
- `pre-commit install` fails (not a git repo, hook path issue).

Auth warnings (gh, kaggle) and `.env` gaps are surfaced but do not stop
the run.
