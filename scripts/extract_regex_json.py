#!/usr/bin/env python3
import argparse
import json
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract page-keyed regex JSON from a TAMU grade distribution PDF."
    )
    parser.add_argument("--pdf", default="GradeDistributionsDB/Fall2023/grd20233DT.pdf")
    parser.add_argument("--output", default="eval_output/dt_fall2023/regex.json")
    return parser


def parse_pdf(pdf_path: Path) -> dict[str, list[dict]]:
    reader = PdfReader(str(pdf_path))
    pages_payload: dict[str, list[dict]] = {}
    current_type = ""
    current_record_id = ""
    current_counts: list[int] = []
    last_section_id = ""

    for page_number, page in enumerate(reader.pages, start=1):
        lines = [line.rstrip() for line in (page.extract_text() or "").splitlines() if line.strip()]
        page_records: list[dict] = []
        record_index = 0

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
            if current_type != "section":
                instructor = None
            gpa = 0.0 if gpa_raw == "Error" else float(gpa_raw)

            page_records.append(
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
                    "record_index": record_index,
                }
            )
            record_index += 1
            current_type = ""
            current_record_id = ""
            current_counts = []

        pages_payload[str(page_number)] = page_records

    return pages_payload


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
