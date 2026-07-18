"""Track B retrieval-augmented per-row predictor (external-knowledge-as-LLM-retrieval).

For each ``(pert, gene)`` this RETRIEVES external biology we hold locally — the
perturbed gene's GO:BP terms plus its functional-category direction prior, the
target gene's GO:BP terms, and (optionally) STRING interaction partners with a
direct pert-gene edge check — assembles them into a context block, and asks
gpt-oss-120b to reason step-by-step and emit a calibrated ``{de_prob, dir_prob}``.
``de_prob`` = P(differentially expressed); ``dir_prob`` = P(up | DE); mapped to
graded ``(up, down) = (de*dir, de*(1-dir))``.

This is the untested "external-knowledge-as-LLM-retrieval" lane: the LLM reasons
over retrieved knowledge as *context*, not over a sparse edge feature or its own
frozen priors. Calibration guard (``findings/track-b-abstention-failure``): the
model is told to express "no effect" as a LOW ``de_prob``, never zero, and any
exact ``(0, 0)`` is floored to the category prior downstream — abstention must
not collapse the rank metric as the prior ReAct agent did (LB 0.488).

Exposes an :data:`AgentFn` ``(pert, gene, seed) -> (up, down)`` so the trial-loop's
``make_agent_row_predictor`` can wire and later evolve it.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from bio_reasoning.features.gene_function import classify, load_go_terms
from bio_reasoning.models.track_a_prior import PRIORS
from bio_reasoning.utils.openai_compat import post_chat_completion

ROOT = Path(__file__).resolve().parents[3]
PERT_CACHE = ROOT / "data" / "interim" / "pert_go_category.json"
GENE_CACHE = ROOT / "data" / "interim" / "gene_go_bp.json"

CELL_DESC = (
    "The cells are mouse bone-marrow-derived macrophages (immune cells). A gene is "
    "'perturbed' by CRISPRi knock-down; we ask how a target gene's expression responds."
)

# llm_fn(prompt, seed) -> (raw_text, token_stats). Injectable so the module is
# offline-testable without a network call.
LlmFn = Callable[[str, int], "tuple[str, dict[str, float]]"]
# string_fn(gene) -> [(partner_symbol, combined_score), ...]. Injectable / optional.
StringFn = Callable[[str], "list[tuple[str, float]]"]


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------


def _dedup(terms: list[str], limit: int) -> list[str]:
    seen: list[str] = []
    for t in terms:
        t = t.strip()
        if t and t != "biological_process" and t not in seen:
            seen.append(t)
        if len(seen) >= limit:
            break
    return seen


def string_partners(gene: str, limit: int = 15) -> list[tuple[str, float]]:
    """Fetch STRING (mouse, species 10090) interaction partners for ``gene``.

    Network call (dev / cache-warming only — Track B inference is offline). Any
    failure degrades to an empty list; never raises.
    """
    url = (
        "https://string-db.org/api/json/interaction_partners?"
        f"identifiers={urllib.parse.quote(gene)}&species=10090&limit={limit}"
    )
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return []
    out: list[tuple[str, float]] = []
    for e in data if isinstance(data, list) else []:
        name = e.get("preferredName_B") or e.get("stringId_B")
        if name:
            out.append((str(name), float(e.get("score", 0.0))))
    return out


@dataclass
class Retrieved:
    """The assembled external-knowledge context for one row + its tool trace."""

    context: str
    prior_up: float
    prior_down: float
    category: str
    direct_edge: bool
    trace: list[dict] = field(default_factory=list)


def retrieve(
    pert: str,
    gene: str,
    *,
    pert_cache: str | Path = PERT_CACHE,
    gene_cache: str | Path = GENE_CACHE,
    string_fn: StringFn | None = None,
    go_limit: int = 12,
) -> Retrieved:
    """Assemble the retrieved-biology context block + tool-call trace for a row.

    Tools: ``get_pert_go_category`` (perturbed gene GO:BP + housekeeping/immune/other
    category → direction prior), ``get_gene_go`` (target gene GO:BP), and — when
    ``string_fn`` is given — ``get_string_partners`` on the perturbed gene with a
    direct pert→gene edge check (the strongest mechanistic direction cue).
    """
    trace: list[dict] = []

    pert_terms = load_go_terms([pert], pert_cache).get(pert, [])
    category = classify(pert, pert_terms)
    u, d = PRIORS[category]
    prior_up, prior_down = d * u, d * (1.0 - u)
    pert_go = _dedup(pert_terms, go_limit)
    trace.append(
        {
            "tool": "get_pert_go_category",
            "arg": pert,
            "result": {"category": category, "n_go": len(pert_go), "prior_up": round(prior_up, 3)},
        }
    )

    gene_terms = load_go_terms([gene], gene_cache).get(gene, [])
    gene_go = _dedup(gene_terms, go_limit)
    trace.append({"tool": "get_gene_go", "arg": gene, "result": {"n_go": len(gene_go)}})

    direct_edge = False
    partners: list[tuple[str, float]] = []
    if string_fn is not None:
        partners = string_fn(pert)
        direct_edge = any(p.lower() == gene.lower() for p, _ in partners)
        trace.append(
            {
                "tool": "get_string_partners",
                "arg": pert,
                "result": {"n_partners": len(partners), "direct_edge_to_target": direct_edge},
            }
        )

    lines = [
        f"PERTURBED gene (knocked down): {pert}",
        f"  functional category: {category}",
        f"  category direction prior: P(up|DE)={u:.2f}, DE-confidence={d:.2f} "
        f"(anchor pred_up={prior_up:.2f}, pred_down={prior_down:.2f})",
        f"  GO biological process: {'; '.join(pert_go) if pert_go else '(none annotated)'}",
        "",
        f"TARGET gene (expression measured): {gene}",
        f"  GO biological process: {'; '.join(gene_go) if gene_go else '(none annotated)'}",
    ]
    if string_fn is not None:
        top = "; ".join(f"{n}({s:.2f})" for n, s in partners[:10])
        lines += [
            "",
            f"STRING interaction partners of {pert}: {top if top else '(none found)'}",
            f"DIRECT {pert}->{gene} interaction edge in STRING: "
            f"{'YES (strong mechanistic link)' if direct_edge else 'no'}",
        ]
    return Retrieved(
        context="\n".join(lines),
        prior_up=prior_up,
        prior_down=prior_down,
        category=category,
        direct_edge=direct_edge,
        trace=trace,
    )


# ---------------------------------------------------------------------------
# Prompt + parse
# ---------------------------------------------------------------------------

_INSTRUCTIONS = """\
You are an expert molecular biologist. {cell_desc}

Task: given RETRIEVED external biology for a CRISPRi perturbation and a target
gene, reason step by step about whether knocking down the perturbed gene changes
the target gene's expression, and in which direction.

Reason explicitly about:
  1. Is the target likely differentially expressed (DE) when the pert is knocked
     down? Shared pathway / GO process, a direct STRING edge, or the pert being a
     broad housekeeping regulator raise DE; unrelated functions lower it.
  2. If DE, is it more likely UP or DOWN? Use the category direction prior as an
     anchor and adjust with the mechanistic evidence.

CALIBRATION IS CRITICAL. The metric ranks rows by confidence (AUROC), so you must
output GRADED probabilities, never hard 0/1 and never a flat 'no effect':
  - de_prob = P(differentially expressed), a real number in [0.05, 0.95].
    Express "probably no effect" as a LOW value like 0.1-0.2 — NEVER 0. A zero
    carries no ranking signal and is penalised.
  - dir_prob = P(up | DE), in [0.05, 0.95].

RETRIEVED CONTEXT
-----------------
{context}
-----------------

After your reasoning, output EXACTLY ONE final line of JSON and nothing after it:
{{"de_prob": <0.05-0.95>, "dir_prob": <0.05-0.95>}}
"""


def build_prompt(retrieved: Retrieved) -> str:
    return _INSTRUCTIONS.format(cell_desc=CELL_DESC, context=retrieved.context)


_JSON_RE = re.compile(r"\{[^{}]*\"de_prob\"[^{}]*\}")


def parse_prediction(text: str) -> tuple[float, float] | None:
    """Extract the last ``{de_prob, dir_prob}`` JSON object from the model text.

    Returns ``(de_prob, dir_prob)`` clamped to ``[0, 1]``, or ``None`` if no
    parseable object is present (caller floors that to the prior).
    """
    matches = _JSON_RE.findall(text or "")
    for blob in reversed(matches):
        try:
            d = json.loads(blob)
            de = float(d["de_prob"])
            dr = float(d["dir_prob"])
        except (ValueError, KeyError, TypeError):
            continue
        return min(max(de, 0.0), 1.0), min(max(dr, 0.0), 1.0)
    return None


def to_up_down(de_prob: float, dir_prob: float) -> tuple[float, float]:
    """Map ``(de_prob, dir_prob=P(up|DE))`` to graded ``(up, down)`` with sum = de_prob."""
    return de_prob * dir_prob, de_prob * (1.0 - dir_prob)


# ---------------------------------------------------------------------------
# Per-row prediction
# ---------------------------------------------------------------------------


@dataclass
class RowResult:
    up: float
    down: float
    de_prob: float | None
    dir_prob: float | None
    category: str
    direct_edge: bool
    parsed: bool
    tokens: dict[str, float]
    trace: list[dict]
    prior_up: float = 0.0
    prior_down: float = 0.0

    @property
    def abstained(self) -> bool:
        """True when the model gave (or defaulted to) a near-no-effect DE call.

        A parse failure counts as abstention; so does a de_prob at/below 0.05.
        This is the metric the dev verify watches for the abstention-collapse.
        """
        return (self.de_prob is None) or (self.de_prob <= 0.05)

    def floored(self) -> tuple[float, float]:
        """``(up, down)`` with an exact ``(0, 0)`` tie replaced by the category prior.

        A raw ``(0, 0)`` carries no rank signal and collapses AUROC
        (``findings/track-b-abstention-failure``); flooring it to the prior keeps
        every row ranked at or above the 0.529 floor. Real signal is untouched.
        """
        if self.up == 0.0 and self.down == 0.0:
            return self.prior_up, self.prior_down
        return self.up, self.down


def predict_row(
    pert: str,
    gene: str,
    seed: int,
    *,
    llm_fn: LlmFn,
    pert_cache: str | Path = PERT_CACHE,
    gene_cache: str | Path = GENE_CACHE,
    string_fn: StringFn | None = None,
) -> RowResult:
    """Retrieve context, call the LLM, parse a calibrated graded ``(up, down)``.

    On parse failure the row returns ``(0, 0)`` — a signal to floor it to the
    category prior downstream (never emit a raw ``0/0`` tie into the metric).
    """
    r = retrieve(pert, gene, pert_cache=pert_cache, gene_cache=gene_cache, string_fn=string_fn)
    prompt = build_prompt(r)
    try:
        text, tokens = llm_fn(prompt, seed)
    except Exception as e:  # a transient failure degrades ONE row, never the run
        r.trace.append({"tool": "llm", "error": str(e)})
        return RowResult(
            0.0,
            0.0,
            None,
            None,
            r.category,
            r.direct_edge,
            False,
            {},
            r.trace,
            prior_up=r.prior_up,
            prior_down=r.prior_down,
        )

    parsed = parse_prediction(text)
    r.trace.append(
        {
            "tool": "llm",
            "parsed": parsed is not None,
            "de_prob": parsed[0] if parsed else None,
            "dir_prob": parsed[1] if parsed else None,
        }
    )
    if parsed is None:
        return RowResult(
            0.0,
            0.0,
            None,
            None,
            r.category,
            r.direct_edge,
            False,
            tokens,
            r.trace,
            prior_up=r.prior_up,
            prior_down=r.prior_down,
        )
    de, dr = parsed
    up, down = to_up_down(de, dr)
    return RowResult(
        up,
        down,
        de,
        dr,
        r.category,
        r.direct_edge,
        True,
        tokens,
        r.trace,
        prior_up=r.prior_up,
        prior_down=r.prior_down,
    )


# ---------------------------------------------------------------------------
# Wiring: AgentFn seam + default OpenRouter LLM
# ---------------------------------------------------------------------------


def make_agent_fn(
    llm_fn: LlmFn,
    *,
    pert_cache: str | Path = PERT_CACHE,
    gene_cache: str | Path = GENE_CACHE,
    string_fn: StringFn | None = None,
) -> Callable[[str, str, int], tuple[float, float]]:
    """Return an ``AgentFn`` ``(pert, gene, seed) -> (up, down)`` for the trial-loop.

    Thin adapter over :func:`predict_row` that drops the trace/metadata so the
    result matches the loop's ``make_agent_row_predictor`` seam.
    """

    def _fn(pert: str, gene: str, seed: int) -> tuple[float, float]:
        res = predict_row(
            pert,
            gene,
            seed,
            llm_fn=llm_fn,
            pert_cache=pert_cache,
            gene_cache=gene_cache,
            string_fn=string_fn,
        )
        return res.up, res.down

    return _fn


def openrouter_llm_fn(
    *,
    api_key: str,
    api_base: str = "https://openrouter.ai/api/v1",
    model: str = "openai/gpt-oss-120b",
    max_tokens: int = 2048,
    reasoning_effort: str = "low",
    timeout_s: int = 120,
    poster: Callable[..., "tuple[str, dict[str, float]]"] = post_chat_completion,
) -> LlmFn:
    """Build an :data:`LlmFn` backed by gpt-oss-120b over OpenRouter (leaderboard-valid)."""

    def _fn(prompt: str, seed: int) -> tuple[str, dict[str, float]]:
        return poster(
            api_base=api_base,
            api_key=api_key,
            model=model,
            prompt=prompt,
            seed=seed,
            max_tokens=max_tokens,
            timeout_s=timeout_s,
            reasoning_effort=reasoning_effort,
        )

    return _fn
