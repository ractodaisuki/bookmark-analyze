from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from bookmark_analyze.ai import build_ai_classifier
from bookmark_analyze.converter import convert_bookmarks


DEFAULT_INPUT = Path("bookmarks/bookmarks.html")
DEFAULT_OUTPUT = Path("ObsidianVault/Bookmarks")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert a Firefox bookmarks.html export into Obsidian markdown notes."
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Firefox bookmarks.html export. Defaults to {DEFAULT_INPUT}.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output Bookmarks directory. Defaults to {DEFAULT_OUTPUT}.",
    )
    parser.add_argument(
        "--ai-provider",
        choices=["openai", "gemini"],
        help="Optional AI classifier provider. Requires bookmark-analyze[ai] and provider API key.",
    )
    parser.add_argument(
        "--ai-model",
        help="Optional AI model override for the selected provider.",
    )
    args = parser.parse_args(argv)

    ai_classifier = build_ai_classifier(args.ai_provider, args.ai_model)
    report = convert_bookmarks(args.input, args.output, ai_classifier=ai_classifier)
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
