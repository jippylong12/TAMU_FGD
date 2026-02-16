#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from tamu_fgd.eval.regex_extractor import parse_pdf


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract page-keyed regex JSON from a TAMU grade distribution PDF."
    )
    parser.add_argument("--pdf", default="GradeDistributionsDB/Fall2023/grd20233DT.pdf")
    parser.add_argument("--output", default="eval_output/dt_fall2023/regex.json")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pdf_path = Path(args.pdf).resolve()
    output_path = Path(args.output).resolve()

    payload = parse_pdf(pdf_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    page_count = len(payload)
    record_count = sum(len(records) for records in payload.values())
    print(f"[OK] Wrote regex output: {output_path}")
    print(f"[SUMMARY] pages={page_count} records={record_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
