# Architecture

System design for the team's pipeline(s) — data flow, components, and the
boundaries between them.

**Status:** placeholder. To be filled as the design lands.

This document will own:

- The high-level data flow from raw Perturb-seq → features → model → submission.
- Component boundaries (data pipeline, inference runner, evaluation, submission).
- Per-track architectural notes (A: prompt engineering, B: agent + tools, C: FT).
- Cross-cutting concerns (config, logging, reproducibility).

Until then, see [`roadmap.md`](roadmap.md) item 5 ("Draft track-specific
approach plans") for the work that will produce the first real draft.
