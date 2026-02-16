#!/usr/bin/env python3
import argparse
import json
import random
import re
from pathlib import Path

from pypdf import PdfReader

SECTION_START_RE = re.compile(r"^([A-Z]{2,6}-\d{3,4}-[A-Z0-9]{3,4})\s+(\d+)\s*$")
COURSE_TOTAL_START_RE = re.compile(r"^COURSE TOTAL:\s*(\d+)\s*$")
DEPT_TOTAL_START_RE = re.compile(r"^DEPARTMENT TOTAL:\s*(\d+)\s*$")
PERCENT_RE = re.compile(r"^\s*\d+(?:\.\d+)?%\s*$")
INT_RE = re.compile(r"^\s*(\d+)\s*$")
SUMMARY_RE = re.compile(
    r"^\s*(\d+)\s+((?:Error)|(?:\d+(?:\.\d+)?))\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*(.*)$"
)
COUNT_KEYS = ["a", "b", "c", "d", "f", "af_total", "i", "s", "u", "q", "x", "grand_total"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare regex PDF parsing vs OpenAI output on random sampled courses.")
    parser.add_argument("--pdf", default="GradeDistributionsDB/Fall2023/grd20233DT.pdf")
    parser.add_argument("--openai-json", default="eval_output/dt_fall2023/openai.json")
    parser.add_argument("--sample-size", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--gpa-tolerance", type=float, default=0.01)
    parser.add_argument("--output", default="eval_output/dt_fall2023/regex_vs_openai_sample.json")
    return parser


def parse_regex_records(pdf_path: Path) -> list[dict]:
    reader = PdfReader(str(pdf_path))
    records = []
    current_type = ""
    current_record_id = ""
    current_counts: list[int] = []
    last_section_id = ""
    for page in reader.pages:
        lines = [line.rstrip() for line in (page.extract_text() or "").splitlines() if line.strip()]
        for line in lines:
            section_match = SECTION_START_RE.match(line)
            if section_match:
                current_type = "section"
                current_record_id = section_match.group(1)
                last_section_id = current_record_id
                current_counts = [int(section_match.group(2))]
                continue

            course_total_match = COURSE_TOTAL_START_RE.match(line)
            if course_total_match:
                current_type = "course_total"
                current_record_id = last_section_id
                current_counts = [int(course_total_match.group(1))]
                continue

            dept_total_match = DEPT_TOTAL_START_RE.match(line)
            if dept_total_match:
                current_type = "department_total"
                current_record_id = "DEPARTMENT_TOTAL"
                current_counts = [int(dept_total_match.group(1))]
                continue

            if not current_type:
                continue
            if PERCENT_RE.match(line):
                continue

            int_match = INT_RE.match(line)
            if int_match and len(current_counts) < 5:
                current_counts.append(int(int_match.group(1)))
                continue

            summary_match = SUMMARY_RE.match(line)
            if not summary_match:
                continue

            while len(current_counts) < 5:
                current_counts.append(0)
            a, b, c, d, f = current_counts[:5]
            af_total = int(summary_match.group(1))
            gpa_raw = summary_match.group(2)
            i_count = int(summary_match.group(3))
            s_count = int(summary_match.group(4))
            u_count = int(summary_match.group(5))
            q_count = int(summary_match.group(6))
            x_count = int(summary_match.group(7))
            grand_total = int(summary_match.group(8))
            instructor = summary_match.group(9).strip() or None
            gpa = 0.0 if gpa_raw == "Error" else float(gpa_raw)

            records.append(
                {
                    "record_type": current_type,
                    "record_id": current_record_id,
                    "counts": {
                        "a": a,
                        "b": b,
                        "c": c,
                        "d": d,
                        "f": f,
                        "af_total": af_total,
                        "i": i_count,
                        "s": s_count,
                        "u": u_count,
                        "q": q_count,
                        "x": x_count,
                        "grand_total": grand_total,
                    },
                    "gpa": gpa,
                    "instructor": instructor,
                }
            )
            current_type = ""
            current_record_id = ""
            current_counts = []
    return records


def course_key(record_id: str) -> str:
    parts = record_id.split("-")
    return f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else record_id


def aggregate_section_courses(records: list[dict]) -> dict[str, dict]:
    courses: dict[str, dict] = {}
    for record in records:
        if record.get("record_type") != "section":
            continue
        key = course_key(str(record.get("record_id", "")))
        counts = record.get("counts", {})
        if key not in courses:
            courses[key] = {k: 0 for k in COUNT_KEYS}
            courses[key]["_gpa_weighted_sum"] = 0.0
        for count_key in COUNT_KEYS:
            courses[key][count_key] += int(counts.get(count_key, 0))
        courses[key]["_gpa_weighted_sum"] += float(record.get("gpa", 0.0)) * int(counts.get("af_total", 0))
    for key, course in courses.items():
        af_total = int(course["af_total"])
        course["gpa"] = round(course["_gpa_weighted_sum"] / af_total, 3) if af_total else 0.0
        del course["_gpa_weighted_sum"]
    return courses


def load_openai_records(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as handle:
        pages = json.load(handle)
    return [record for page_records in pages.values() for record in page_records]


def main() -> int:
    args = build_parser().parse_args()
    pdf_path = Path(args.pdf).resolve()
    openai_path = Path(args.openai_json).resolve()
    output_path = Path(args.output).resolve()

    regex_courses = aggregate_section_courses(parse_regex_records(pdf_path))
    openai_courses = aggregate_section_courses(load_openai_records(openai_path))
    common_courses = sorted(set(regex_courses.keys()) & set(openai_courses.keys()))
    if not common_courses:
        print("[ERROR] No common courses found between regex and OpenAI outputs.")
        return 2

    rng = random.Random(args.seed)
    sample_size = min(args.sample_size, len(common_courses))
    sampled = sorted(rng.sample(common_courses, sample_size))
    comparisons = []
    for course in sampled:
        left = regex_courses[course]
        right = openai_courses[course]
        count_mismatches = {
            key: {"regex": left[key], "openai": right[key]}
            for key in COUNT_KEYS
            if int(left[key]) != int(right[key])
        }
        gpa_diff = abs(float(left["gpa"]) - float(right["gpa"]))
        gpa_match = gpa_diff <= args.gpa_tolerance
        comparisons.append(
            {
                "course": course,
                "match": (not count_mismatches) and gpa_match,
                "count_mismatches": count_mismatches,
                "gpa": {"regex": left["gpa"], "openai": right["gpa"], "diff": round(gpa_diff, 6), "match": gpa_match},
            }
        )

    matched = sum(1 for item in comparisons if item["match"])
    payload = {
        "pdf": str(pdf_path),
        "openai_json": str(openai_path),
        "seed": args.seed,
        "sample_size": sample_size,
        "gpa_tolerance": args.gpa_tolerance,
        "summary": {
            "common_courses": len(common_courses),
            "sampled_courses": sample_size,
            "matched_courses": matched,
            "mismatched_courses": sample_size - matched,
        },
        "comparisons": comparisons,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(f"[OK] Wrote comparison report: {output_path}")
    print(
        "[SUMMARY] "
        f"common={len(common_courses)} sampled={sample_size} matched={matched} mismatched={sample_size - matched}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
