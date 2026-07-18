# Team knowledge layers

Directories under `knowledge/`, each with a clear job. `raw/` and the local
`source/` are **flat** — no type subfolders, type lives in frontmatter
(`source_type:`).

| Layer | What it holds | In git? |
|---|---|---|
| [`knowledge/raw/`](../raw/) | Native source artifacts (PDFs, HTML, .docx), flat | **gitignored** — local cache only |
| [`knowledge/source/`](../source/) | **Local ingest front door.** One distilled markdown page per artifact, flat, with provenance frontmatter. Written by `/wiki-ingest`. | yes |
| `knowledge/domains/<domain>/source/` | **Read-only synced mirror** of the central `knowledge-base` repo (per-domain). Every page carries a `<!-- synced from knowledge-base — do not edit here -->` marker. Fed by `/knowledge-sync` + the human-gated `promote`, **never** by `/wiki-ingest`. | yes (mirror) |
| [`knowledge/wiki/`](.) | Hand-curated synthesis: home / index / log / findings / methods / decisions / concepts | yes |

### Two source layers, one lifecycle

`source/` (flat, local) and `domains/<domain>/source/` (synced, read-only) are the
**same content class at two stages of one pipeline**, not competing layouts:

```
/wiki-ingest → knowledge/source/<stem>.md   (flat, editable, project-local)
   → promote (human-gated) → central knowledge-base SSOT
   → /knowledge-sync → knowledge/domains/<domain>/source/  (read-only mirror here)
   → retire the flat copy, repoint index links
```

So: **ingest flat, promote up, sync down.** Never write into `domains/` directly —
it's a mirror; the next sync clobbers local edits. To change a synced page, edit it
upstream in `knowledge-base` and re-pull.

> **Mid-migration caveat (2026-07):** the domains/ migration and the knowledge-base
> subscription are **in progress and incomplete**. Today the corpus straddles both
> layouts — ~90 un-migrated flat pages plus ~200 synced domain pages — and skill/collection
> naming isn't fully standardized yet. Treat the pipeline above as the intended end-state,
> not a finished fact. Don't assume every flat page has a domain twin, or vice versa.

## Reliability order — wiki > web > model knowledge

When answering a question, sources rank in this order:

1. **The wiki first** (`knowledge/source/` + `knowledge/wiki/`) — cited, curated,
   ground-truth for this project.
2. **Web second** — WebFetch / WebSearch when the wiki is silent. Cite
   the URL inline. If the source proves useful, ingest it via
   `/wiki-ingest` so the next query lands at step 1.
3. **Model knowledge last** — only when both above fail. Mark the
   answer as "model knowledge, not from wiki/web" so the reader knows.

Don't skip ahead. The wiki is the team's compounding memory; bypassing
it makes it stale.

Rule of thumb:

- A teammate asks "what does paper X say?" → `source/<x>.md` (or `domains/<domain>/source/<x>.md` if synced)
- A teammate asks "what did we decide about Y?" → `wiki/decisions/<y>.md`
- A teammate asks "what have we learned across N sources?" → `wiki/findings/<topic>.md`

`source/` is regenerable from its citation; never hand-edit a distilled
page — re-ingest instead. `wiki/` is the opposite: synthesis you wrote,
no automatic regeneration.

## When to add to which layer

| You have | Goes in |
|---|---|
| A paper you read | `/wiki-ingest <arxiv-url>` → writes `source/<stem>.md` (type `papers` in frontmatter) |
| A blog post or doc page | `/wiki-ingest <url>` → writes `source/<stem>.md` (type `web`) |
| A repo worth remembering | `/wiki-ingest <github-url>` → writes `source/<stem>.md` (type `repos`) |
| A talk or conference video | `/wiki-ingest <url>` → writes `source/<stem>.md` (type `talks`) |
| A cross-source insight | Hand-author or `/wiki-learn` → writes `wiki/findings/<topic>.md` |
| A method we tried + outcome | Hand-author → `wiki/methods/<name>.md` |
| A team decision + rationale | Hand-author → `wiki/decisions/<topic>.md` |
| An entity / concept spanning many sources | Hand-author → `wiki/concepts/<name>.md` |

If a teammate would want to read it on their phone (PDF, slides,
screenshot), it does NOT live in any of these layers — it lives in
Drive (private — shared with the team).
Link to the Drive original via `drive:` in the source page's frontmatter.

## How to ingest

Use **`/wiki-ingest <url-or-path>`**. It reads the source, drafts a
distilled markdown page with citations, and proposes the write under your
approval. No silent writes.

For knowledge that came out of a conversation (not a fetchable artifact),
use **`/wiki-learn`** to distill the current session into one or more
pages.

### Practical flow by source type

| Source | Step 1 | Step 2 |
|---|---|---|
| **arXiv paper** | `/wiki-ingest <arxiv-url>` | Optionally upload PDF to Drive `02-papers/`, paste link as `drive:` in the source page's frontmatter |
| **Blog post / docs page** | `/wiki-ingest <url>` | — (no separate artifact) |
| **Non-arXiv PDF / slides** | Upload to Drive `02-papers/`, download a local copy | `/wiki-ingest <local-path>`, add `drive:` link to frontmatter |
| **Notion / Slack thread** | Paste relevant text into a local `.md` file | `/wiki-ingest <local-path>` |
| **Conversation insight** | `/wiki-learn` (no fetch needed) | — |

### Decision rule

**Prefer URL over PDF.** WebFetch works without auth and produces clean
markdown. Use a local PDF only when no usable URL exists.

- **`source/`** = "what's in this one artifact + why we care" — distilled, agent-searchable.
- **`wiki/`** = synthesis across many sources — what we *think*, not what they *said*.
- **Drive** = the original artifact you can read in full — linked from `source/` via `drive:`, not searched directly.

### Anyone can ingest

Not a curator role. Three guardrails keep it safe:

1. **Approval gate** in the skill (nothing lands without `y`).
2. **PR review** — wiki changes go through normal git flow.
3. **`/wiki-lint`** periodically catches orphans, missing cites, stale claims.

## How to query

Use **`/wiki-query <question>`**. It searches `source/` and `wiki/`,
follows citations, synthesizes an answer with inline cites, and
optionally files the answer back as a new page in `wiki/findings/`.

**Search backend (optional):** if you have [qmd](https://github.com/tobi/qmd)
installed and a `bio-reasoning` collection registered, `/wiki-query` uses
hybrid BM25 + vector + rerank search. Otherwise it falls back to plain
`grep` over `source/` and `wiki/`. qmd is a personal speedup, not a team
dependency.

## How to keep it healthy

Run **`/wiki-lint`** periodically (or `/wiki-lint --fix`) to find orphans,
broken cites, and missing cross-references.

## Conventions

- One source page per artifact. Filename `kebab-case.md`.
- `source/` frontmatter:
  ```yaml
  ---
  source_url: <url or "local file: <path>">
  source_type: papers      # or web, repos, talks, notion, slack
  title: <human title>
  author: <author>
  retrieved: <YYYY-MM-DD>
  drive: <drive-link>      # optional — link to original artifact
  ---
  ```
- `wiki/` frontmatter (looser; synthesis is hand-authored):
  ```yaml
  ---
  title: <human title>
  cites:
    - <path to source/ page or url>
  ---
  ```
- Body: distilled summary first (3–6 lines), then sections as needed.
- Cross-link with `[[other-page-slug]]` (resolved relative to `knowledge/`).
  When you cross-link across layers, add the target to `cites:`.
- Update [`index.md`](index.md) when adding a page (the skills do this).

## Wiki subdirectories (synthesis)

```
knowledge/wiki/
├── README.md      # this file
├── home.md        # project orientation, entry point for queries
├── index.md       # catalog of source/ AND wiki/ pages
├── log.md         # append-only history of ingests + queries
├── findings/      # cross-source synthesis answering specific questions
├── methods/       # methods we tried, with rationale + outcome
├── decisions/     # decisions with rationale
└── concepts/      # entity / concept pages spanning multiple sources
```

Subdirectories grow as needed — don't pre-create empty ones.
