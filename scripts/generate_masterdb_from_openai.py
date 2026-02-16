#!/usr/bin/env python3
import argparse
import csv
import json
import shutil
from collections import defaultdict
from pathlib import Path

HEADER = [
    "Course",
    "Professor",
    "GPA",
    "% of A's",
    "% of B's",
    "% of C's",
    "% of D's",
    "% of F's",
    "% of Q Drop's",
    "% of Semesters",
]
BLANK_LINE = ["", "", "", "", "", "", "", "", ""]
COURSE_LINE = ["", "", "", "", "", "", "", ""]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate MasterDB.csv from one or more OpenAI openai.json files."
    )
    parser.add_argument(
        "--openai-json",
        action="append",
        default=[],
        help="Path to openai.json (repeatable).",
    )
    parser.add_argument(
        "--eval-output",
        action="append",
        default=[],
        help="Path to eval output dir containing openai.json (repeatable).",
    )
    parser.add_argument(
        "--output-csv",
        default="GradeDistributionsDB/MasterDBs/MasterDB.csv",
        help="Path to write MasterDB.csv.",
    )
    parser.add_argument(
        "--frontend-root",
        default="",
        help="Optional TAMU_FGD_FRONT_END root path; publishes to MasterDBs/MasterDB.csv.",
    )
    parser.add_argument(
        "--default-instructor",
        default="NOT LISTED",
        help="Fallback instructor name when missing.",
    )
    parser.add_argument("--verbose", action="store_true", help="Print progress details.")
    return parser


def as_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def percent(numerator: float, denominator: float) -> str:
    if denominator <= 0:
        return "0%"
    return f"{round((numerator * 100.0) / denominator, 2)}%"


def gpa_from_counts(stats: dict) -> float:
    af_total = stats["af_total"]
    if af_total <= 0:
        return 0.0
    points = (4.0 * stats["a"]) + (3.0 * stats["b"]) + (2.0 * stats["c"]) + stats["d"]
    return round(points / af_total, 2)


def course_from_record_id(record_id: str) -> str:
    parts = (record_id or "").split("-")
    if len(parts) < 2:
        return ""
    return f"{parts[0].upper()}-{parts[1]}"


def normalize_sources(args) -> list[Path]:
    sources = []
    for raw_path in args.openai_json:
        sources.append(Path(raw_path).resolve())
    for output_dir in args.eval_output:
        sources.append((Path(output_dir).resolve() / "openai.json"))

    deduped = []
    seen = set()
    for path in sources:
        key = str(path)
        if key not in seen:
            seen.add(key)
            deduped.append(path)
    if not deduped:
        raise RuntimeError("No input provided. Use --openai-json or --eval-output.")
    return deduped


def aggregate_openai_json(path: Path, master: dict, default_instructor: str, verbose: bool) -> None:
    with open(path, "r", encoding="utf-8") as handle:
        pages = json.load(handle)
    seen_pairs = set()
    section_count = 0

    for page_key in sorted(pages.keys(), key=lambda item: int(item) if str(item).isdigit() else str(item)):
        for record in pages.get(page_key, []):
            if record.get("record_type") != "section":
                continue
            course = course_from_record_id(record.get("record_id", ""))
            if not course:
                continue
            instructor = (record.get("instructor") or "").strip() or default_instructor
            counts = record.get("counts") or {}
            stats = master[course][instructor]
            stats["a"] += as_float(counts.get("a"))
            stats["b"] += as_float(counts.get("b"))
            stats["c"] += as_float(counts.get("c"))
            stats["d"] += as_float(counts.get("d"))
            stats["f"] += as_float(counts.get("f"))
            stats["q"] += as_float(counts.get("q"))
            stats["af_total"] += as_float(counts.get("af_total"))
            stats["total"] += as_float(counts.get("af_total")) + as_float(counts.get("q"))
            pair = (course, instructor)
            if pair not in seen_pairs:
                stats["semesters"] += 1
                seen_pairs.add(pair)
            section_count += 1

    if verbose:
        print(f"[OPENAI] Processed {section_count} section rows from {path}")


def write_masterdb(master: dict, output_csv: Path) -> int:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    professor_rows = 0
    with open(output_csv, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        for course in sorted(master.keys()):
            course_line = list(COURSE_LINE)
            course_line[0] = course
            writer.writerow(course_line)
            for instructor in sorted(master[course].keys()):
                stats = master[course][instructor]
                total = stats["total"]
                writer.writerow(
                    [
                        "",
                        instructor,
                        gpa_from_counts(stats),
                        percent(stats["a"], total),
                        percent(stats["b"], total),
                        percent(stats["c"], total),
                        percent(stats["d"], total),
                        percent(stats["f"], total),
                        percent(stats["q"], total),
                        str(int(stats["semesters"])),
                    ]
                )
                professor_rows += 1
            writer.writerow(BLANK_LINE)
    return professor_rows


def publish_to_frontend(output_csv: Path, frontend_root: Path) -> Path:
    destination = frontend_root / "MasterDBs" / "MasterDB.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output_csv, destination)
    return destination


def main() -> int:
    args = build_parser().parse_args()
    try:
        sources = normalize_sources(args)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        return 2

    master = defaultdict(
        lambda: defaultdict(
            lambda: {"a": 0.0, "b": 0.0, "c": 0.0, "d": 0.0, "f": 0.0, "q": 0.0, "af_total": 0.0, "total": 0.0, "semesters": 0}
        )
    )
    for source in sources:
        if not source.exists():
            print(f"[ERROR] Missing input file: {source}")
            return 2
        aggregate_openai_json(source, master, args.default_instructor, args.verbose)

    output_csv = Path(args.output_csv).resolve()
    professor_rows = write_masterdb(master, output_csv)
    print(f"[OK] Wrote MasterDB CSV: {output_csv}")
    print(f"[SUMMARY] files={len(sources)} courses={len(master)} professors={professor_rows}")

    if args.frontend_root:
        frontend_root = Path(args.frontend_root).resolve()
        destination = publish_to_frontend(output_csv, frontend_root)
        print(f"[OK] Published frontend CSV: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
