from __future__ import annotations

import argparse
import json

from common import run_chat_completion


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test a configured LLM provider.")
    parser.add_argument(
        "--provider",
        default=None,
        choices=["gpt_oss", "openai_compatible", "openai", "azure", "azure_openai", "anthropic"],
        help="Provider override. Defaults to BIOREASONING_LLM_PROVIDER from env.",
    )
    parser.add_argument("--prompt", default="Reply with exactly: smoke test ok")
    parser.add_argument("--system-prompt", default=None)
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--reasoning-effort", default="low", choices=["low", "medium", "high"])
    args = parser.parse_args()

    result = run_chat_completion(
        prompt=args.prompt,
        provider=args.provider,
        system_prompt=args.system_prompt,
        max_tokens=args.max_tokens,
        reasoning_effort=args.reasoning_effort,
    )

    print(
        json.dumps(
            {
                "provider": result.provider,
                "model": result.model,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "total_tokens": result.total_tokens,
                "text": result.text,
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
