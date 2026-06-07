# Team wiki

Distilled, cited knowledge for the BioReasoning Challenge 2026 team.

This is where we capture **what we learned** — not raw artifacts (those go
to [Drive](https://drive.google.com/drive/folders/1kE-JCKUJowtu7XFn5LALDt9xEq1DYBxS)),
not code (`src/`), not personal notes (use your own scratch).

## When to add a page

Add a wiki page when you have **distilled, cited** knowledge another
teammate would benefit from in a week or a month:

- A paper's key claim and how it applies to our problem.
- A method we tried, why we chose it, what we learned.
- A decision with rationale we'll forget without writing it down.

If it's a raw PDF, put it in Drive `02-papers/`. If it's a one-off run
output, leave it in `outputs/` and decide later whether to distill it.

## How to add a page

Use **`/wiki-ingest <url-or-path>`**. It reads the source, drafts a
distilled markdown page with citations, and proposes the write under your
approval. No silent writes.

For knowledge that came out of a conversation (not a fetchable artifact),
use **`/wiki-learn`** to distill the current session into one or more
pages.

### Practical flow by source type

| Source | Step 1 | Step 2 |
|---|---|---|
| **arXiv paper** | `/wiki-ingest <arxiv-url>` | Optionally upload PDF to Drive `02-papers/`, paste link as `drive:` in the page's frontmatter |
| **Blog post / docs page** | `/wiki-ingest <url>` | — (no separate artifact) |
| **Non-arXiv PDF / slides** | Upload to Drive `02-papers/`, download a local copy | `/wiki-ingest <local-path>`, add `drive:` link to frontmatter |
| **Notion / Slack thread** | Paste relevant text into a local `.md` file | `/wiki-ingest <local-path>` |
| **Conversation insight** | `/wiki-learn` (no fetch needed) | — |

### Decision rule

**Prefer URL over PDF.** WebFetch works without auth and produces clean
markdown. Use a local PDF only when no usable URL exists.

- **Wiki** = "what's in it + why we care" — distilled, in git, agent-searchable.
- **Drive** = "the original artifact you can read in full" — PDFs, slides,
  screenshots. Linked from the wiki via `drive:`, not searched directly.

If a teammate can answer a question from the wiki page alone, ingest
succeeded. If they need the original, they click `drive:`.

### Anyone can ingest

Not a curator role. Three guardrails keep it safe:

1. **Approval gate** in the skill (nothing lands without `y`).
2. **PR review** — wiki changes go through normal git flow.
3. **`/wiki-lint`** periodically catches orphans, missing cites, stale claims.

## How to query

Use **`/wiki-query <question>`**. It searches the wiki, follows citations,
synthesizes an answer with inline cites, and optionally files the answer
back as a new page.

**Search backend (optional):** if you have [qmd](https://github.com/jmsung/qmd)
installed and a `bio-reasoning` collection registered, `/wiki-query` uses
hybrid BM25 + vector + rerank search. Otherwise it falls back to plain
`grep` over the wiki — works fine for a small wiki, slower for a large
one. qmd is a personal speedup, not a team dependency.

## How to keep it healthy

Run **`/wiki-lint`** periodically (or `/wiki-lint --fix`) to find orphans,
broken cites, and missing cross-references.

## Conventions

- One page per concept. Filename `kebab-case.md`.
- Frontmatter:
  ```yaml
  ---
  title: <human title>
  cites:
    - <url or path>
  source_type: papers      # or web, repos, talks, methods, decisions
  retrieved: <YYYY-MM-DD>  # for fetched sources
  ---
  ```
- Body: distilled summary first (3–6 lines), then sections as needed.
- Cross-link with `[[other-page-slug]]` (resolved relative to
  `docs/wiki/`). When you cross-link to a page in a different
  subdirectory, also add the target to `cites:`.
- Update [`index.md`](index.md) when adding a page (the skills do this).

## Layout

```
docs/wiki/
├── README.md      # this file — conventions
├── home.md        # project orientation, entry point for queries
├── index.md       # catalog of all pages
├── papers/        # distilled paper summaries
├── web/           # web-source distillations
├── repos/         # repo summaries
├── talks/         # talk distillations
├── methods/       # methods we tried, with rationale
├── decisions/     # decisions with rationale
└── findings/      # cross-cutting synthesis answering specific questions
```

Subdirectories grow as needed — don't pre-create empty ones.
