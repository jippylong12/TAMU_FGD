#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tamu_fgd.eval.comparison import compare_section_records
from tamu_fgd.eval.legacy_extractor import LegacyPageExtractor
from tamu_fgd.eval.openai_extractor import OpenAIPageExtractor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare legacy extraction vs OpenAI extraction for one PDF."
    )
    parser.add_argument("--pdf", required=True, help="Path to target PDF.")
    parser.add_argument("--output-dir", default="eval_output", help="Directory for JSON outputs.")
    parser.add_argument("--model", default="gpt-4.1-mini", help="OpenAI model for extraction.")
    parser.add_argument("--max-pages", type=int, default=None, help="Optional page limit.")
    parser.add_argument(
        "--skip-openai",
        action="store_true",
        help="Run legacy extraction only (no OpenAI calls).",
    )
    return parser


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def main() -> int:
    args = build_parser().parse_args()
    pdf_path = Path(args.pdf).resolve()
    output_dir = Path(args.output_dir).resolve()

    legacy = LegacyPageExtractor().extract(pdf_path=pdf_path, max_pages=args.max_pages)
    legacy_path = output_dir / "legacy.json"
    write_json(legacy_path, legacy)
    print(f"[OK] Wrote legacy output: {legacy_path}")

    if args.skip_openai:
        print("[DONE] Legacy extraction only.")
        return 0

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY is not set.")
        return 2

    openai = OpenAIPageExtractor(api_key=api_key, model=args.model).extract(
        pdf_path=pdf_path,
        max_pages=args.max_pages,
    )
    openai_path = output_dir / "openai.json"
    write_json(openai_path, openai)
    print(f"[OK] Wrote OpenAI output: {openai_path}")

    report = compare_section_records(legacy=legacy, openai=openai)
    report_path = output_dir / "comparison.json"
    write_json(report_path, report)
    summary = report["summary"]
    print(f"[OK] Wrote comparison output: {report_path}")
    print(
        "[SUMMARY] "
        f"pages={summary['pages_compared']} "
        f"compared={summary['section_records_compared']} "
        f"matches={summary['exact_matches']} "
        f"mismatches={summary['mismatches']} "
        f"match_rate={summary['match_rate']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
