#!/usr/bin/env python3
import argparse
import json
import random
from pathlib import Path

COUNT_KEYS = ["a", "b", "c", "d", "f", "af_total", "i", "s", "u", "q", "x", "grand_total"]
REQUIRED_RECORD_KEYS = {"record_type", "record_id", "counts", "gpa", "instructor", "record_index"}
OPTIONAL_RECORD_KEYS = {"honors"}
COUNT_KEY_SET = set(COUNT_KEYS)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare regex vs OpenAI semester outputs on sampled colleges.")
    parser.add_argument("--regex-root", default="eval_output/fall2023_all_regex")
    parser.add_argument("--openai-root", default="eval_output/fall2023_all")
    parser.add_argument("--sample-size", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--gpa-tolerance", type=float, default=0.01)
    parser.add_argument("--output", default="eval_output/fall2023_all_regex/regex_vs_openai_college_sample.json")
    return parser


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def schema_issues(payload: dict, label: str) -> list[str]:
    issues: list[str] = []
    if not isinstance(payload, dict):
        return [f"{label}: root is not an object"]
    for page, records in payload.items():
        if not isinstance(page, str):
            issues.append(f"{label}: page key is not string")
            continue
        if not isinstance(records, list):
            issues.append(f"{label}: page {page} is not an array")
            continue
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                issues.append(f"{label}: page {page} record {index} is not an object")
                continue
            record_keys = set(record.keys())
            if not REQUIRED_RECORD_KEYS.issubset(record_keys):
                issues.append(f"{label}: page {page} record {index} is missing required record keys")
                continue
            if not record_keys.issubset(REQUIRED_RECORD_KEYS | OPTIONAL_RECORD_KEYS):
                issues.append(f"{label}: page {page} record {index} has unexpected record keys")
                continue
            if "honors" in record and not isinstance(record.get("honors"), bool):
                issues.append(f"{label}: page {page} record {index} honors is not a boolean")
                continue
            counts = record.get("counts")
            if not isinstance(counts, dict):
                issues.append(f"{label}: page {page} record {index} counts is not an object")
                continue
            if set(counts.keys()) != COUNT_KEY_SET:
                issues.append(f"{label}: page {page} record {index} has unexpected count keys")
    return issues


def flatten_records(payload: dict) -> list[dict]:
    keys = sorted(payload.keys(), key=lambda key: int(key) if key.isdigit() else key)
    records: list[dict] = []
    for key in keys:
        records.extend(payload.get(key, []))
    return records


def aggregate_sections(records: list[dict]) -> dict[str, dict]:
    courses: dict[str, dict] = {}
    for record in records:
        if record.get("record_type") != "section":
            continue
        rid = str(record.get("record_id", ""))
        parts = rid.split("-")
        course = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else rid
        counts = record.get("counts", {})
        if course not in courses:
            courses[course] = {key: 0 for key in COUNT_KEYS}
            courses[course]["_gpa_sum"] = 0.0
        for key in COUNT_KEYS:
            courses[course][key] += int(counts.get(key, 0))
        courses[course]["_gpa_sum"] += float(record.get("gpa", 0.0)) * int(counts.get("af_total", 0))
    for course, data in courses.items():
        af_total = int(data["af_total"])
        data["gpa"] = round(data["_gpa_sum"] / af_total, 3) if af_total else 0.0
        del data["_gpa_sum"]
    return courses


def aggregate_summary(regex_courses: dict[str, dict], openai_courses: dict[str, dict], tol: float) -> dict:
    regex_keys = set(regex_courses.keys())
    openai_keys = set(openai_courses.keys())
    common = sorted(regex_keys & openai_keys)
    missing_in_regex = sorted(openai_keys - regex_keys)
    missing_in_openai = sorted(regex_keys - openai_keys)
    mismatches = []
    for course in common:
        left = regex_courses[course]
        right = openai_courses[course]
        count_keys = [key for key in COUNT_KEYS if int(left.get(key, 0)) != int(right.get(key, 0))]
        gpa_diff = abs(float(left.get("gpa", 0.0)) - float(right.get("gpa", 0.0)))
        if count_keys or gpa_diff > tol:
            mismatches.append({"course": course, "count_mismatch_keys": count_keys, "gpa_diff": round(gpa_diff, 6)})
    return {
        "regex_courses": len(regex_keys),
        "openai_courses": len(openai_keys),
        "common_courses": len(common),
        "missing_in_regex": missing_in_regex,
        "missing_in_openai": missing_in_openai,
        "mismatched_courses_count": len(mismatches),
        "mismatched_courses_preview": mismatches[:20],
    }


def compare_college(name: str, regex_path: Path, openai_path: Path, tol: float) -> dict:
    regex_payload = load_json(regex_path)
    openai_payload = load_json(openai_path)
    regex_issues = schema_issues(regex_payload, "regex")
    openai_issues = schema_issues(openai_payload, "openai")
    schema_match = not regex_issues and not openai_issues
    page_keys_match = set(regex_payload.keys()) == set(openai_payload.keys())
    regex_records = flatten_records(regex_payload)
    openai_records = flatten_records(openai_payload)
    summary = aggregate_summary(aggregate_sections(regex_records), aggregate_sections(openai_records), tol)
    aggregate_match = (
        len(summary["missing_in_regex"]) == 0
        and len(summary["missing_in_openai"]) == 0
        and summary["mismatched_courses_count"] == 0
    )
    return {
        "college_dir": name,
        "regex_path": str(regex_path),
        "openai_path": str(openai_path),
        "schema_match": schema_match,
        "page_keys_match": page_keys_match,
        "regex_schema_issues": regex_issues[:20],
        "openai_schema_issues": openai_issues[:20],
        "record_count_regex": len(regex_records),
        "record_count_openai": len(openai_records),
        "aggregate_match": aggregate_match,
        "aggregate_summary": summary,
        "match": schema_match and page_keys_match and aggregate_match,
    }


def main() -> int:
    args = build_parser().parse_args()
    regex_root = Path(args.regex_root).resolve()
    openai_root = Path(args.openai_root).resolve()
    output_path = Path(args.output).resolve()
    regex_dirs = {entry.name for entry in regex_root.iterdir() if entry.is_dir() and (entry / "regex.json").exists()}
    openai_dirs = {entry.name for entry in openai_root.iterdir() if entry.is_dir() and (entry / "openai.json").exists()}
    common = sorted(regex_dirs & openai_dirs)
    if not common:
        print("[ERROR] No overlapping college outputs found.")
        return 2
    sample_size = min(args.sample_size, len(common))
    sampled = sorted(random.Random(args.seed).sample(common, sample_size))
    results = [
        compare_college(name, regex_root / name / "regex.json", openai_root / name / "openai.json", args.gpa_tolerance)
        for name in sampled
    ]
    matched = sum(1 for item in results if item["match"])
    payload = {
        "regex_root": str(regex_root),
        "openai_root": str(openai_root),
        "seed": args.seed,
        "sample_size": sample_size,
        "gpa_tolerance": args.gpa_tolerance,
        "summary": {
            "common_colleges": len(common),
            "sampled_colleges": sample_size,
            "matched_colleges": matched,
            "mismatched_colleges": sample_size - matched,
        },
        "results": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(f"[OK] Wrote comparison report: {output_path}")
    print(f"[SUMMARY] common={len(common)} sampled={sample_size} matched={matched} mismatched={sample_size - matched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
