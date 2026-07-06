from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd
from common import ROOT, run_chat_completion

from mlgenx import format_prompt, parse_answer

TRACK_A_SAMPLE = ROOT / "configs" / "sample_submissions" / "track_a_sample_submission.csv"
TRACK_B_SAMPLE = ROOT / "configs" / "sample_submissions" / "track_b_sample_submission.csv"
TRACK_B_SYSTEM_PROMPT = ROOT / "configs" / "track_b_system_prompt.txt"
SEEDS = [42, 43, 44]


def append_answer_tag(prompt: str) -> str:
    return (
        f"{prompt.rstrip()}\n\n"
        "Return ONLY the final choice in this exact format:\n"
        "<answer>A</answer>, <answer>B</answer>, or <answer>C</answer>\n"
        "Do not include any other text."
    )


def extract_answer_tag(text: str) -> str | None:
    match = re.search(r"<answer>\s*([ABCabc])\s*</answer>", text)
    return match.group(1).upper() if match else None


def validate_schema(output_df: pd.DataFrame, sample_path: Path) -> list[str]:
    sample_df = pd.read_csv(sample_path)
    missing = [col for col in sample_df.columns if col not in output_df.columns]
    extra = [col for col in output_df.columns if col not in sample_df.columns]
    if missing or extra:
        raise ValueError(
            f"Schema mismatch for {sample_path.name}: missing={missing}, extra={extra}"
        )
    return list(sample_df.columns)


def build_track_a_rows(
    df: pd.DataFrame, provider: str | None, max_tokens: int, reasoning_effort: str
) -> pd.DataFrame:
    rows_out = []
    for _, row in df.iterrows():
        prompt = append_answer_tag(format_prompt(row["pert"], row["gene"]))
        seed_payloads: dict[int, dict[str, object]] = {}
        for seed in SEEDS:
            response = run_chat_completion(
                prompt=prompt,
                provider=provider,
                max_tokens=max_tokens,
                reasoning_effort=reasoning_effort,
            )
            answer_source = extract_answer_tag(response.text) or response.text
            pred_up, pred_down = parse_answer(answer_source)
            seed_payloads[seed] = {
                "prediction_up": pred_up,
                "prediction_down": pred_down,
                "trace": response.text,
                "tokens": response.total_tokens,
                "prompt_tokens": response.prompt_tokens,
                "model": response.model,
            }

        rows_out.append(
            {
                "id": row["id"],
                "prediction_up": sum(seed_payloads[s]["prediction_up"] for s in SEEDS) / len(SEEDS),
                "prediction_down": sum(seed_payloads[s]["prediction_down"] for s in SEEDS)
                / len(SEEDS),
                "prediction_up_seed42": seed_payloads[42]["prediction_up"],
                "prediction_down_seed42": seed_payloads[42]["prediction_down"],
                "prediction_up_seed43": seed_payloads[43]["prediction_up"],
                "prediction_down_seed43": seed_payloads[43]["prediction_down"],
                "prediction_up_seed44": seed_payloads[44]["prediction_up"],
                "prediction_down_seed44": seed_payloads[44]["prediction_down"],
                "reasoning_trace_seed42": seed_payloads[42]["trace"],
                "reasoning_trace_seed43": seed_payloads[43]["trace"],
                "reasoning_trace_seed44": seed_payloads[44]["trace"],
                "tokens_used": int(sum(seed_payloads[s]["tokens"] for s in SEEDS)),
                "prompt_tokens": int(max(seed_payloads[s]["prompt_tokens"] for s in SEEDS)),
                "model_name": seed_payloads[42]["model"],
            }
        )
    return pd.DataFrame(rows_out)


def build_track_b_rows(
    df: pd.DataFrame, provider: str | None, max_tokens: int, reasoning_effort: str
) -> pd.DataFrame:
    system_prompt = TRACK_B_SYSTEM_PROMPT.read_text().strip()
    rows_out = []
    for _, row in df.iterrows():
        user_prompt = append_answer_tag(format_prompt(row["pert"], row["gene"]))
        response = run_chat_completion(
            prompt=user_prompt,
            provider=provider,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
        )
        answer_source = extract_answer_tag(response.text) or response.text
        pred_up, pred_down = parse_answer(answer_source)
        rows_out.append(
            {
                "id": row["id"],
                "prediction_up": pred_up,
                "prediction_down": pred_down,
                "reasoning_trace": response.text,
                "tokens_used": int(response.total_tokens),
                "num_tool_calls": 0,
                "prompt_tokens": int(response.prompt_tokens),
                "num_distinct_tools": 0,
                "model_name": response.model,
            }
        )
    return pd.DataFrame(rows_out)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke test Track A/B schema against a selected provider."
    )
    parser.add_argument("--track", required=True, choices=["a", "b"])
    parser.add_argument(
        "--provider",
        default=None,
        choices=["gpt_oss", "openai_compatible", "openai", "azure", "azure_openai", "anthropic"],
        help="Provider override. Defaults to BIOREASONING_LLM_PROVIDER from env.",
    )
    parser.add_argument("--rows", type=int, default=1)
    parser.add_argument("--test-csv", type=Path, default=ROOT / "data" / "raw" / "test.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "smoke")
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--reasoning-effort", default="low", choices=["low", "medium", "high"])
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.test_csv).head(args.rows)
    if df.empty:
        raise ValueError(f"No rows found in {args.test_csv}")

    if args.track == "a":
        output_df = build_track_a_rows(df, args.provider, args.max_tokens, args.reasoning_effort)
        sample_path = TRACK_A_SAMPLE
    else:
        output_df = build_track_b_rows(df, args.provider, args.max_tokens, args.reasoning_effort)
        sample_path = TRACK_B_SAMPLE

    column_order = validate_schema(output_df, sample_path)
    output_df = output_df[column_order]

    output_path = (
        args.output_dir / f"track_{args.track}_{(args.provider or 'env')}_smoke_submission.csv"
    )
    output_df.to_csv(output_path, index=False)
    print(
        json.dumps(
            {
                "track": args.track,
                "provider": args.provider or "env",
                "rows": len(output_df),
                "output_path": str(output_path),
                "columns": list(output_df.columns),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
