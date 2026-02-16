import re

SECTION_START_RE = re.compile(r"^([A-Z]{2,6}-\d{3,4}-[A-Z0-9]{3,4})\s+(\d+)\s*$")
COURSE_TOTAL_START_RE = re.compile(r"^COURSE TOTAL:\s*(\d+)\s*$")
DEPT_TOTAL_START_RE = re.compile(r"^DEPARTMENT TOTAL:\s*(\d+)\s*$")
PERCENT_RE = re.compile(r"^\s*\d+(?:\.\d+)?%\s*$")
SUMMARY_WITH_Q_RE = re.compile(
    r"^\s*(\d+)\s+((?:Error)|(?:\d+(?:\.\d+)?))\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*(.*)$"
)
INTS_IN_LINE_RE = re.compile(r"\d+")


def build_record(
    record_type: str,
    record_id: str,
    a: int,
    b: int,
    c: int,
    d: int,
    f_count: int,
    af_total: int,
    i_count: int,
    s_count: int,
    u_count: int,
    q_count: int,
    x_count: int,
    grand_total: int,
    gpa: float,
    instructor: str | None,
    record_index: int,
) -> dict:
    return {
        "record_type": record_type,
        "record_id": record_id,
        "counts": {
            "a": a,
            "b": b,
            "c": c,
            "d": d,
            "f": f_count,
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


def parse_standard_summary(line: str) -> dict | None:
    match = SUMMARY_WITH_Q_RE.match(line)
    if not match:
        return None
    return {
        "af_total": int(match.group(1)),
        "gpa_raw": match.group(2),
        "i": int(match.group(3)),
        "s": int(match.group(4)),
        "u": int(match.group(5)),
        "q": int(match.group(6)),
        "x": int(match.group(7)),
        "grand_total": int(match.group(8)),
        "instructor": match.group(9).strip() or None,
    }


def parse_standard_page(lines: list[str]) -> list[dict]:
    current_type = ""
    current_record_id = ""
    current_counts: list[int] = []
    last_section_id = ""
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

        if not current_type or PERCENT_RE.match(line):
            continue

        summary = parse_standard_summary(line)
        if not summary:
            tokens = [int(token) for token in INTS_IN_LINE_RE.findall(line)]
            if len(tokens) == 1:
                current_counts.append(tokens[0])
            continue

        while len(current_counts) < 5:
            current_counts.append(0)
        a, b, c, d, f_count = current_counts[:5]
        gpa = 0.0 if summary["gpa_raw"] == "Error" else float(summary["gpa_raw"])
        instructor = summary["instructor"] if current_type == "section" else None
        page_records.append(
            build_record(
                current_type,
                current_record_id,
                a,
                b,
                c,
                d,
                f_count,
                summary["af_total"],
                summary["i"],
                summary["s"],
                summary["u"],
                summary["q"],
                summary["x"],
                summary["grand_total"],
                gpa,
                instructor,
                record_index,
            )
        )
        record_index += 1
        current_type = ""
        current_record_id = ""
        current_counts = []

    return page_records
