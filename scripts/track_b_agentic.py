"""
Track B -- Agentic tool-use baseline using DSPy ReAct.

Runs a ReAct agent loop where the LLM reasons in text, decides which tools
to call, and iterates until it produces a final answer.  Uses DSPy's
text-based tool calling which works with any instruction-following model
(no native function-calling API support required).

Ships with these working tools:

  1. lookup_pert          -- what genes are affected by a perturbation?
  2. lookup_gene          -- what perturbations affect a gene?
  3. direction_prior      -- evidence-grounded graded direction prior (the floor)
  4. gene_info            -- fetch gene annotations from mygene.info
  5. protein_interactions -- fetch protein interactions from STRING DB
  6. submit_graded        -- submit graded up/down probabilities (preferred)
  7. submit_answer        -- submit a hard A/B/C answer (fallback)

Participants should extend or replace these with their own tools.

Usage:
    pip install -e .          # from repo root -- installs mlgenx
    pip install dspy
    python examples/track_b_agentic.py \\
        --api-base http://your-endpoint/v1 \\
        --api-key YOUR_KEY \\
        --model openai/gpt-oss-120b
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import threading
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

import dspy
import pandas as pd
from dotenv import load_dotenv
from tools.direction_prior import blend, direction_prior, floor_to_prior, prior_scores

from mlgenx import format_prompt, parse_answer
from mlgenx.prompts import _PROMPT_ZERO, CELL_DESC

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.local", override=True)
DEFAULT_DATA_DIR = ROOT / "data" / "raw" / "track_a"  # Track B data == Track A (byte-identical)
TEST_CSV = Path(os.getenv("BIOREASONING_TEST_CSV", str(DEFAULT_DATA_DIR / "test.csv")))
TRAIN_CSV = Path(os.getenv("BIOREASONING_TRAIN_CSV", str(DEFAULT_DATA_DIR / "train.csv")))

_TRAIN_DF: pd.DataFrame | None = None


def _set_train_df(df: pd.DataFrame) -> None:
    """Override the training frame the lookup tools see. Used by --eval to
    restrict tools to the fold's disjoint train partition (leak-free CV)."""
    global _TRAIN_DF
    _TRAIN_DF = df.reset_index(drop=True)


def _get_train_df() -> pd.DataFrame:
    global _TRAIN_DF
    if _TRAIN_DF is None:
        _TRAIN_DF = pd.read_csv(TRAIN_CSV)
    return _TRAIN_DF


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

_LABEL_STR = {
    "up": "up-regulated",
    "down": "down-regulated",
    "none": "not differentially expressed",
}


def lookup_pert(pert: str) -> str:
    """Look up all training examples where a given gene was knocked down
    (CRISPRi perturbation).  Returns a summary of target genes grouped by
    label (up-regulated, down-regulated, or not differentially expressed).
    Use this to understand the downstream effects of perturbing a gene."""
    df = _get_train_df()
    hits = df[df["pert"].str.lower() == pert.lower()]
    if hits.empty:
        return f"No training examples found for perturbation '{pert}'."

    lab = hits["label"].astype(str).str.lower()
    up_genes = hits[lab == "up"]["gene"].tolist()
    down_genes = hits[lab == "down"]["gene"].tolist()
    none_genes = hits[lab == "none"]["gene"].tolist()

    lines = [f"Training data for perturbation '{pert}' ({len(hits)} examples):"]
    lines.append(
        f"  Summary: {len(up_genes)} up-regulated, "
        f"{len(down_genes)} down-regulated, "
        f"{len(none_genes)} not differentially expressed"
    )
    if up_genes:
        lines.append(f"    Up-regulated: {', '.join(up_genes[:30])}")
    if down_genes:
        lines.append(f"    Down-regulated: {', '.join(down_genes[:30])}")
    if none_genes:
        lines.append(f"    Not differentially expressed: {', '.join(none_genes[:30])}")
    return "\n".join(lines)


def lookup_gene(gene: str) -> str:
    """Look up all training examples where a given gene was the measurement
    target (its expression was checked after some perturbation).  Returns
    which perturbations led to up-, down-, or no regulation of this gene.
    Use this to understand what regulates a gene."""
    df = _get_train_df()
    hits = df[df["gene"].str.lower() == gene.lower()]
    if hits.empty:
        return f"No training examples found for target gene '{gene}'."

    lines = [f"Training data for target gene '{gene}' ({len(hits)} examples):"]
    for _, r in hits.iterrows():
        lab = str(r["label"]).lower()
        label_str = _LABEL_STR.get(lab, str(r["label"]))
        lines.append(f"  - pert={r['pert']}: {label_str}")
    return "\n".join(lines)


def submit_answer(answer: str, reasoning: str = "") -> str:
    """Submit your final answer to the gene expression question.  You MUST
    call this tool when you have reached a conclusion.  The answer parameter
    must be exactly 'A', 'B', or 'C'."""
    answer = answer.strip().upper()
    if answer not in ("A", "B", "C"):
        return f"Error: answer must be 'A', 'B', or 'C', got '{answer}'."
    return f"Answer recorded: {answer}"


def _clamp_pair(up: float, down: float) -> tuple[float, float]:
    """Clamp each score to [0,1]; renormalize if they sum above 1."""
    up = min(max(up, 0.0), 1.0)
    down = min(max(down, 0.0), 1.0)
    if up + down > 1.0:
        s = up + down
        up, down = up / s, down / s
    return up, down


def submit_graded(prediction_up: float, prediction_down: float, reasoning: str = "") -> str:
    """Submit GRADED probabilities instead of a hard A/B/C letter. Provide
    P(up-regulated) and P(down-regulated), each in [0,1] with their sum <= 1
    (the remainder is P(not differentially expressed)). PREFER this over
    submit_answer: the metric is AUROC, so calibrated confidence (e.g. 0.7/0.1)
    scores far better than a hard 1/0. Anchor these on direction_prior's graded
    scores, then adjust up or down with mechanistic and network evidence. Call
    exactly once when you have reached a conclusion."""
    try:
        up, down = _clamp_pair(float(prediction_up), float(prediction_down))
    except (TypeError, ValueError):
        return "Error: prediction_up and prediction_down must be numbers in [0,1]."
    return f"Graded prediction recorded: up={up:.3f}, down={down:.3f}, none={1 - up - down:.3f}."


def gene_info(gene_symbol: str) -> str:
    """Look up annotations for a mouse gene from mygene.info, including
    gene name, summary, Gene Ontology biological process terms, and KEGG
    pathways."""
    url = (
        f"https://mygene.info/v3/query?"
        f"q=symbol:{gene_symbol}&species=mouse"
        f"&fields=symbol,name,summary,go.BP,pathway.kegg&size=1"
    )
    try:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return f"Error querying mygene.info for {gene_symbol}: {e}"

    hits = data.get("hits", [])
    if not hits:
        return f"No results found for gene symbol '{gene_symbol}' in mouse."

    hit = hits[0]
    lines = [f"Gene: {hit.get('symbol', gene_symbol)}"]

    name = hit.get("name")
    if name:
        lines.append(f"Full name: {name}")

    summary = hit.get("summary")
    if summary:
        lines.append(f"Summary: {summary}")

    go_bp = hit.get("go", {}).get("BP", [])
    if isinstance(go_bp, dict):
        go_bp = [go_bp]
    if go_bp:
        terms = list({t["term"] for t in go_bp if "term" in t})[:8]
        if terms:
            lines.append(f"GO Biological Process ({len(terms)} shown): " + "; ".join(terms))

    pathways = hit.get("pathway", {}).get("kegg", [])
    if isinstance(pathways, dict):
        pathways = [pathways]
    if pathways:
        pnames = [p.get("name", p.get("id", "?")) for p in pathways][:5]
        lines.append("KEGG Pathways: " + "; ".join(pnames))

    return "\n".join(lines)


def protein_interactions(gene_symbol: str, limit: int = 10) -> str:
    """Fetch known protein-protein interactions for a mouse gene from
    STRING DB.  Returns up to 10 interaction partners with combined
    confidence scores."""
    limit = min(max(1, limit), 50)
    url = (
        f"https://string-db.org/api/json/interaction_partners?"
        f"identifiers={gene_symbol}&species=10090&limit={limit}"
    )
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return f"Error querying STRING DB for {gene_symbol}: {e}"

    if not data:
        return f"No protein interactions found for '{gene_symbol}' " f"in mouse (STRING DB)."

    lines = [f"Protein interactions for {gene_symbol} (mouse, STRING DB):"]
    for entry in data[:limit]:
        partner = entry.get("preferredName_B", entry.get("stringId_B", "?"))
        score = entry.get("score", 0)
        lines.append(f"  - {partner} (combined score: {score:.3f})")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tokens_from_history(lm: dspy.LM, start_idx: int) -> int:
    """Sum total_tokens from LM history entries added since start_idx."""
    total = 0
    for entry in lm.history[start_idx:]:
        if isinstance(entry, dict):
            usage = entry.get("usage") or {}
            if isinstance(usage, dict):
                total += usage.get("total_tokens", 0)
            else:
                total += getattr(usage, "total_tokens", 0) or 0
        elif hasattr(entry, "usage"):
            u = entry.usage
            total += getattr(u, "total_tokens", 0) if u else 0
    return total


def extract_answer_tag(text: str) -> str | None:
    m = re.search(r"<answer>\s*([ABCabc])\s*</answer>", text)
    return m.group(1).upper() if m else None


def load_cache(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {}


def save_cache(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2))


# ---------------------------------------------------------------------------
# DSPy signature
# ---------------------------------------------------------------------------


class BioPredict(dspy.Signature):
    """You are an expert molecular biologist who studies gene expression
    using Perturb-seq.  Use the available tools to look up training data
    and gene annotations, then call submit_answer with your final choice
    (A, B, or C)."""

    question: str = dspy.InputField(desc="Gene expression prediction question with answer choices")
    answer: str = dspy.OutputField(desc="Your answer: A, B, or C, with brief justification")


# ---------------------------------------------------------------------------
# Reusable agent runner (shared by main() and the trial-loop --track b adapter)
# ---------------------------------------------------------------------------


def default_tools() -> list:
    """The Track B tool set (single source for main() and the trial-loop)."""
    return [
        lookup_pert,
        lookup_gene,
        direction_prior,
        gene_info,
        protein_interactions,
        submit_graded,
        submit_answer,
    ]


def build_openrouter_lm(max_tokens: int = 16384, max_retries: int = 2) -> "dspy.LM":
    """The fixed challenge model (gpt-oss-120b) via OpenRouter — leaderboard-valid."""
    or_model = os.getenv("BIOREASONING_OPENROUTER_MODEL", "openai/gpt-oss-120b")
    litellm_model = or_model if or_model.startswith("openrouter/") else f"openrouter/{or_model}"
    return dspy.LM(
        model=litellm_model,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        max_tokens=max_tokens,
        temperature=1.0,
        num_retries=max_retries,
    )


def build_react_agent(lm: "dspy.LM", max_iters: int, tools: list | None = None) -> "dspy.ReAct":
    """Configure DSPy with ``lm`` and return a ReAct agent over the Track B tools."""
    dspy.configure(lm=lm, adapter=dspy.ChatAdapter(use_native_function_calling=False))
    return dspy.ReAct(
        BioPredict, tools=tools if tools is not None else default_tools(), max_iters=max_iters
    )


def extract_prediction(
    trace: Any,
    final_text: str,
    pert: str,
    prior_fn: Callable[[str], tuple[float, float]] = prior_scores,
) -> tuple[float, float]:
    """Map an agent trace + final answer to graded ``(up, down)``.

    Preference order (this is the exact logic that governs the rank-metric score;
    emitting 0/0 on abstention is what collapsed LB to 0.488):
      1. ``submit_graded`` args → clamped graded pair (best — continuous scores).
      2. ``submit_answer`` A/B/C → hard pair via ``parse_answer``.
      3. an ``<answer>`` tag / free-text parse of ``final_text``.
      4. neither parseable → the evidence prior for ``pert`` (never a blind 1/3).
    """
    graded: tuple[float, float] | None = None
    submitted: str | None = None
    for k in sorted(trace.keys() if isinstance(trace, dict) else []):
        if not k.startswith("tool_name_"):
            continue
        step = k.split("_")[-1]
        args_d = trace.get(f"tool_args_{step}", {}) or {}
        if trace[k] == "submit_graded":
            try:
                graded = _clamp_pair(
                    float(args_d.get("prediction_up")),
                    float(args_d.get("prediction_down")),
                )
            except (TypeError, ValueError):
                graded = None
        elif trace[k] == "submit_answer":
            submitted = (args_d.get("answer", "") or "").strip().upper()

    if graded is not None:
        return graded
    if submitted in ("A", "B", "C"):
        return parse_answer(submitted)

    tag = extract_answer_tag(final_text)
    source = tag if tag else (final_text or "")
    pred = parse_answer(source, default=(None, None)) if source else (None, None)  # type: ignore[arg-type]
    if pred == (None, None):
        try:
            pred = prior_fn(pert)
        except Exception:
            pred = parse_answer("")
    return pred


def predict_row(
    react: Any,
    pert: str,
    gene: str,
    prior_fn: Callable[[str], tuple[float, float]] = prior_scores,
) -> tuple[float, float]:
    """Run the ReAct ``react`` agent on one (pert, gene) row → graded ``(up, down)``.

    ``react`` is any callable returning an object with ``.answer`` and
    ``.trajectory`` (so it can be faked in tests). A raised agent falls back to the
    evidence prior via :func:`extract_prediction`.
    """
    try:
        result = react(question=format_prompt(pert, gene))
        final_text = getattr(result, "answer", "") or ""
        trace = getattr(result, "trajectory", {}) or {}
    except Exception:
        final_text, trace = "", {}
    return extract_prediction(trace, final_text, pert, prior_fn=prior_fn)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DEFAULT_SYSTEM_PROMPT_PATH = ROOT / "configs" / "track_b_system_prompt.txt"


def main() -> None:
    parser = argparse.ArgumentParser(description="Track B: Agentic tool-use baseline (DSPy ReAct)")
    parser.add_argument(
        "--api-base",
        default=os.getenv("BIOREASONING_OPENAI_API_BASE", "http://localhost:8000/v1"),
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv(
            "BIOREASONING_OPENAI_API_KEY",
            os.getenv("OPENAI_API_KEY", "token-abc123"),
        ),
    )
    parser.add_argument(
        "--model",
        default=os.getenv("BIOREASONING_OPENAI_MODEL", "openai/gpt-oss-120b"),
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=int(os.getenv("BIOREASONING_MAX_COMPLETION_TOKENS", "65536")),
    )
    parser.add_argument("--timeout-s", type=int, default=240)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument(
        "--reasoning-effort",
        default=os.getenv("BIOREASONING_REASONING_EFFORT", "medium"),
        choices=["low", "medium", "high"],
        help="Reasoning effort level sent to the model (default: medium).",
    )
    parser.add_argument(
        "--system-prompt",
        type=Path,
        default=DEFAULT_SYSTEM_PROMPT_PATH,
        help="Path to system prompt file (contents used as-is).",
    )
    parser.add_argument(
        "--max-iters",
        type=int,
        default=40,
        help="Max ReAct iterations (tool-call rounds per row). Real rows finish "
        "in <10; the low default caps runaway rows where the adapter can't parse "
        "the model's output and would otherwise loop to the competition ceiling "
        "(250) burning ~10x the tokens. Raise toward 250 only if legitimate rows "
        "hit the cap.",
    )
    parser.add_argument("--test-csv", type=Path, default=TEST_CSV)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "track_b" / "default")
    parser.add_argument("--save-every", type=int, default=5)
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Number of concurrent rows to process. Increase to speed up.",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Delete cached API responses and start fresh.",
    )
    parser.add_argument(
        "--model-name",
        default=None,
        help="Override model name recorded in submission (defaults to --model).",
    )
    parser.add_argument(
        "--provider",
        default=os.getenv("BIOREASONING_LLM_PROVIDER", "openai_compatible"),
        choices=["openai_compatible", "openrouter", "anthropic", "openai"],
        help="LLM provider. 'openai_compatible' = local vLLM/Ollama gpt-oss-120b; "
        "'openrouter' = hosted gpt-oss-120b via OpenRouter (both are the fixed "
        "challenge model — leaderboard-valid). 'anthropic'/'openai' = hosted "
        "frontier dev fallbacks for harness debugging only (NOT leaderboard-valid).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N rows (dev smoke run).",
    )
    parser.add_argument(
        "--eval",
        action="store_true",
        help="Leak-free eval mode: run on a labeled holdout from TRAIN_CSV "
        "(see --split for fold vs dual-OOD holdout) and score with "
        "mean(AUROC_de,AUROC_dir) vs the split's prior floor. Tools are "
        "restricted to the eval split's train partition.",
    )
    parser.add_argument("--eval-n", type=int, default=None, help="Cap holdout rows in --eval.")
    parser.add_argument(
        "--fold-k", type=int, default=5, help="CV folds for --eval split (fold mode)."
    )
    parser.add_argument("--fold-seed", type=int, default=0, help="Seed for the --eval split.")
    parser.add_argument(
        "--split",
        default="fold",
        choices=["fold", "holdout"],
        help="--eval split: 'fold' = doubly_disjoint_folds (legacy leak-free CV); "
        "'holdout' = holdout_split dual-OOD val (perts+genes disjoint — the "
        "authoritative fitness gate; baselines: no-signal 0.500, prior 0.533).",
    )
    parser.add_argument(
        "--blend-alpha",
        type=float,
        default=1.0,
        help="Blend agent predictions with the direction prior: "
        "final = alpha*agent + (1-alpha)*prior. 1.0 (default) = agent-only with "
        "floor-to-prior on (0,0) ties; <1.0 mixes the prior into every row "
        "(any alpha<1 also lifts the ties). Tune on --split holdout.",
    )
    args = parser.parse_args()
    if not 0.0 <= args.blend_alpha <= 1.0:
        parser.error("--blend-alpha must be in [0, 1].")

    model_name = args.model_name or args.model

    system_prompt = args.system_prompt.read_text().strip()
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        prompt_tokens = len(enc.encode(system_prompt))
    except Exception:
        prompt_tokens = len(system_prompt) // 4  # rough fallback
    print(
        f"System prompt loaded from {args.system_prompt} "
        f"({len(system_prompt)} chars, ~{prompt_tokens} tokens)"
    )
    if prompt_tokens > 16384:
        parser.error(
            f"System prompt is ~{prompt_tokens} tokens, exceeds 16,384 limit. "
            f"Shorten {args.system_prompt} and retry."
        )

    # ── Configure DSPy ────────────────────────────────────────────────
    # NOTE: 'anthropic' and 'openai' are DEV fallbacks (hosted frontier models)
    # for debugging the harness only — NOT the fixed challenge model, so their
    # output is never leaderboard-valid. The real run uses gpt-oss-120b via the
    # 'openai_compatible' provider (Bing's Ollama/vLLM endpoint).
    if args.provider == "openrouter":
        # Hosted gpt-oss-120b via OpenRouter — the fixed challenge model,
        # leaderboard-valid. Cheap pay-per-token; pair with --limit for smoke tests.
        or_model = os.getenv("BIOREASONING_OPENROUTER_MODEL", "openai/gpt-oss-120b")
        model_name = args.model_name or or_model
        lm = build_openrouter_lm(args.max_tokens, args.max_retries)
    elif args.provider == "anthropic":
        claude_model = os.getenv("BIOREASONING_ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        litellm_model = (
            claude_model if claude_model.startswith("anthropic/") else f"anthropic/{claude_model}"
        )
        model_name = args.model_name or litellm_model
        lm = dspy.LM(
            model=litellm_model,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=min(args.max_tokens, 8192),  # Claude output cap
            temperature=1.0,
            num_retries=args.max_retries,
        )
    elif args.provider == "openai":
        # Hosted OpenAI (api.openai.com) — cheap small model for smoke tests.
        # No api_base (litellm defaults to OpenAI); no reasoning_effort (only
        # valid for o-series/gpt-5). Pair with --limit to keep cost negligible.
        dev_model = os.getenv("BIOREASONING_OPENAI_DEV_MODEL", "gpt-4o-mini")
        litellm_model = dev_model if dev_model.startswith("openai/") else f"openai/{dev_model}"
        model_name = args.model_name or litellm_model
        lm = dspy.LM(
            model=litellm_model,
            api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=min(args.max_tokens, 4096),
            temperature=1.0,
            num_retries=args.max_retries,
        )
    else:
        # litellm model format: "openai/<model_name_on_server>". The "openai/"
        # prefix selects the OpenAI-compatible provider and is stripped before
        # the request is sent. The vLLM/Ollama server registers the model as
        # "openai/gpt-oss-120b", so we always prepend "openai/".
        litellm_model = args.model if args.model.startswith("openai/") else f"openai/{args.model}"
        lm = dspy.LM(
            model=litellm_model,
            api_base=args.api_base,
            api_key=args.api_key,
            max_tokens=args.max_tokens,
            temperature=1.0,
            num_retries=args.max_retries,
            reasoning_effort=args.reasoning_effort,
            allowed_openai_params=["reasoning_effort"],
        )
    tool_list = default_tools()
    if len(tool_list) > 100:
        parser.error(f"Too many tools ({len(tool_list)}), competition limit is 100.")
    print(f"Tools: {len(tool_list)}, max_iters: {args.max_iters}")
    react = build_react_agent(lm, args.max_iters, tool_list)

    # ── Load data and cache ───────────────────────────────────────────
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cache_path = args.output_dir / "responses_cache.json"
    if args.clear_cache and cache_path.exists():
        cache_path.unlink()
        print("Cleared response cache.")
    cache = load_cache(cache_path)
    if "rows" not in cache:
        cache["rows"] = {}

    eval_labels = None
    if args.eval:
        # Leak-free eval: hold out labeled rows from train and restrict the lookup
        # tools to the TRAIN partition so the agent can't read a holdout row's own
        # label. 'fold' = doubly-disjoint CV fold; 'holdout' = the dual-OOD val
        # split (perts+genes disjoint — the authoritative fitness gate).
        from bio_reasoning.eval.split import (
            assert_leak_free,
            doubly_disjoint_folds,
            holdout_split,
        )

        train_full = pd.read_csv(TRAIN_CSV)
        if args.split == "holdout":
            tr_idx, ev_idx = holdout_split(train_full, seed=args.fold_seed)
        else:
            tr_idx, ev_idx = doubly_disjoint_folds(train_full, k=args.fold_k, seed=args.fold_seed)[
                0
            ]
        # The whole eval's validity rests on zero pert/gene overlap — fail loud if
        # column names or hashing ever drift.
        assert_leak_free(train_full, tr_idx, ev_idx)
        _set_train_df(train_full.iloc[tr_idx])  # tools see disjoint train only
        ev = train_full.iloc[ev_idx].reset_index(drop=True)
        if args.eval_n is not None:
            ev = ev.head(args.eval_n).reset_index(drop=True)
        test_df = pd.DataFrame(
            {
                "id": ev["pert"].astype(str) + "_" + ev["gene"].astype(str),
                "pert": ev["pert"],
                "gene": ev["gene"],
            }
        )
        eval_labels = ev["label"].astype(str).to_numpy()
        split_desc = (
            f"dual-OOD holdout (seed={args.fold_seed})"
            if args.split == "holdout"
            else f"fold k={args.fold_k} seed={args.fold_seed}"
        )
        print(
            f"--eval: leak-free {args.split} on {len(test_df)} holdout rows "
            f"({split_desc}); tools restricted to {len(tr_idx)} disjoint train rows."
        )
    else:
        test_df = pd.read_csv(args.test_csv)
        if args.limit is not None:
            test_df = test_df.head(args.limit).reset_index(drop=True)
            print(f"--limit {args.limit}: processing first {len(test_df)} rows only (dev smoke).")
    total = len(test_df)
    cache_lock = threading.Lock()
    new_count = 0

    def process_row(idx: int, row: pd.Series) -> None:
        nonlocal new_count
        rid = row["id"]

        with cache_lock:
            if rid in cache["rows"] and "prediction_up" in cache["rows"][rid]:
                print(f"[{idx+1}/{total}] {rid} cache_hit")
                return

        user_prompt = format_prompt(row["pert"], row["gene"])

        tool_calls_count = 0
        tokens = 0
        trace: Any = {}

        history_before = len(lm.history)
        try:
            result = react(question=user_prompt)
            final_text = result.answer or ""
            trajectory = getattr(result, "trajectory", {}) or {}
            trace = trajectory
            tool_calls_count = sum(
                1 for k in trajectory if isinstance(k, str) and k.startswith("tool_name")
            )
        except Exception as e:
            print(f"  [error] ReAct failed: {e}")
            final_text = ""
            trace = {"error": str(e)}
        tokens = _tokens_from_history(lm, history_before)

        # Prefer graded → hard A/B/C → free-text tag → evidence prior (never 0/0).
        pred_up, pred_down = extract_prediction(trace, final_text, row["pert"])

        with cache_lock:
            cache["rows"][rid] = {
                "prediction_up": pred_up,
                "prediction_down": pred_down,
                "reasoning_trace": json.dumps(trace, default=str),
                "tokens_used": tokens,
                "num_tool_calls": tool_calls_count,
                "model_name": model_name,
            }
            new_count += 1
            print(
                f"[{idx+1}/{total}] {rid} pred_up={pred_up:.3f} "
                f"pred_down={pred_down:.3f} "
                f"tools={tool_calls_count} tokens={tokens}"
            )
            if new_count % args.save_every == 0:
                save_cache(cache_path, cache)

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(process_row, idx, row) for idx, row in test_df.iterrows()]
        for future in as_completed(futures):
            future.result()

    save_cache(cache_path, cache)
    print(f"Collected {total} rows ({new_count} new API calls)")

    # ── Build submission CSV ──────────────────────────────────────────
    rows_out = []
    for _, row in test_df.iterrows():
        rid = row["id"]
        c = cache["rows"].get(rid, {})
        agent_up = c.get("prediction_up", 0.0)
        agent_down = c.get("prediction_down", 0.0)
        if args.blend_alpha < 1.0:
            # Mix the prior into every row (any alpha<1 lifts (0,0) ties too).
            # Note: unlike floor-to-prior, a failed/missing (0,0) row blends to
            # (1-alpha)*prior — a shrunk prior, not the full floor.
            pred_up, pred_down = blend(agent_up, agent_down, row["pert"], args.blend_alpha)
        else:
            # Default: floor only zero-signal (0,0) ties to the prior so no row is
            # a rank-metric tie (PR #13 root cause: 72% ties → LB 0.488). A missing
            # /failed row defaults to (0,0) so it floors to the prior too.
            pred_up, pred_down = floor_to_prior(agent_up, agent_down, row["pert"])
        rows_out.append(
            {
                "id": rid,
                "prediction_up": pred_up,
                "prediction_down": pred_down,
                "reasoning_trace": c.get("reasoning_trace", ""),
                "tokens_used": int(c.get("tokens_used", 0)),
                "num_tool_calls": int(c.get("num_tool_calls", 0)),
                "prompt_tokens": prompt_tokens,
                "num_distinct_tools": len(tool_list),
                "model_name": c.get("model_name", model_name),
            }
        )

    sub_df = pd.DataFrame(rows_out)
    sub_path = args.output_dir / "submission.csv"
    sub_df.to_csv(sub_path, index=False)

    if args.eval:
        # Score the labeled holdout with the shared Track A/B metric and compare
        # to the 0.529 floor. The Kaggle zip below is submission-only, so return.
        from bio_reasoning.eval.track_a_score import score_preds

        up = sub_df["prediction_up"].to_numpy(dtype=float)
        down = sub_df["prediction_down"].to_numpy(dtype=float)
        # Reference baseline on the same split: the dual-OOD holdout has an honest
        # prior floor of 0.533 (no-signal 0.500); the fold CV compares to LB 0.529.
        floor = 0.533 if args.split == "holdout" else 0.529
        try:
            s = score_preds(eval_labels, up, down)
        except ValueError as e:
            print(
                f"\n[eval] Cannot score {len(sub_df)} holdout rows — degenerate "
                f"class balance ({e}). Re-run with a larger --eval-n."
            )
            return
        metrics = {
            "n_rows": int(len(sub_df)),
            "split": args.split,
            # fold_k is meaningless for the holdout split (it uses no folds)
            **({"fold_k": args.fold_k} if args.split == "fold" else {}),
            "fold_seed": args.fold_seed,
            "model_name": model_name,
            "auroc_de": float(s["auroc_de"]),
            "auroc_dir": float(s["auroc_dir"]),
            "mean": float(s["mean"]),
            "prior_floor": floor,
            "beats_floor": bool(s["mean"] > floor),
        }
        metrics_path = args.output_dir / "eval_metrics.json"
        metrics_path.write_text(json.dumps(metrics, indent=2))
        verdict = "BEATS" if s["mean"] > floor else "does NOT beat"
        title = "dual-OOD val" if args.split == "holdout" else "leak-free CV"
        print(
            f"\n=== Track B {title} ({len(sub_df)} rows, split={args.split}) ===\n"
            f"  mean(AUROC_de, AUROC_dir) = {s['mean']:.3f}  "
            f"(de={s['auroc_de']:.3f}, dir={s['auroc_dir']:.3f})\n"
            f"  vs prior floor {floor:.3f} -> {verdict} the floor\n"
            f"Wrote {sub_path}\nWrote {metrics_path}"
        )
        return

    prompt_path = args.output_dir / "prompt.txt"
    prompt_path.write_text(
        "# System prompt used for Track B (DSPy ReAct)\n\n"
        + system_prompt
        + "\n\n# User prompt template (zero-shot)\n\n"
        + _PROMPT_ZERO.format(pert="{pert}", gene="{gene}", cell_desc=CELL_DESC)
    )

    out_tools = args.output_dir / "tools"
    if out_tools.exists():
        shutil.rmtree(out_tools)
    src_tools = Path(__file__).resolve().parent / "tools"
    if src_tools.exists():
        shutil.copytree(src_tools, out_tools)
    else:
        out_tools.mkdir()
        (out_tools / "__init__.py").write_text("")

    zip_path = args.output_dir / "submission_track_b.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(sub_path, "submission.csv")
        zf.write(prompt_path, "prompt.txt")
        zf.write(args.system_prompt, args.system_prompt.name)
        for tool_file in out_tools.rglob("*.py"):
            zf.write(tool_file, f"tools/{tool_file.name}")

    print(f"Wrote {sub_path}")
    print(f"Wrote {prompt_path}")
    print(f"Wrote {zip_path}  <-- upload this to Kaggle")


if __name__ == "__main__":
    main()
