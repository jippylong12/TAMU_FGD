import re
from tamu_fgd.eval.regex_extractor_standard import (
    COURSE_TOTAL_START_RE,
    DEPT_TOTAL_START_RE,
    INTS_IN_LINE_RE,
    PERCENT_RE,
    SECTION_START_RE,
    build_record,
)
SECTION_PROF_RE = re.compile(r"^([A-Z]{2,6}-\d{3,4}-[A-Z0-9]{3,4})\s+((?:Error)|(?:\d+(?:\.\d+)?))\s*(.*)$")
SUMMARY_NO_Q_RE = re.compile(
    r"^\s*(\d+)\s+((?:Error)|(?:\d+(?:\.\d+)?))\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*(.*)$"
)
SUMMARY_NO_Q_LEAD_RE = re.compile(
    r"^\s*(\d+)\s+(\d+)\s+((?:Error)|(?:\d+(?:\.\d+)?))\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*(.*)$"
)

def parse_prof_summary(line: str) -> dict | None:
    match = SUMMARY_NO_Q_RE.match(line)
    if match:
        return {
            "style": "no_q",
            "af_total": int(match.group(1)),
            "gpa_raw": match.group(2),
            "i": int(match.group(3)),
            "s": int(match.group(4)),
            "u": int(match.group(5)),
            "q": 0,
            "x": int(match.group(6)),
            "grand_total": int(match.group(7)),
            "instructor": match.group(8).strip() or None,
        }
    match = SUMMARY_NO_Q_LEAD_RE.match(line)
    if match:
        return {
            "style": "no_q_lead",
            "af_total": int(match.group(2)),
            "gpa_raw": match.group(3),
            "i": int(match.group(4)),
            "s": int(match.group(5)),
            "u": int(match.group(6)),
            "q": 0,
            "x": int(match.group(7)),
            "grand_total": int(match.group(8)),
            "instructor": match.group(9).strip() or None,
        }
    return None

def parse_prof_page(lines: list[str]) -> list[dict]:
    current_type = ""
    current_record_id = ""
    current_counts: list[int] = []
    current_gpa_override: float | None = None
    current_instructor_override: str | None = None
    last_section_id = ""
    pending_prof_sections: list[dict] = []
    page_records: list[dict] = []
    record_index = 0

    for line in lines:
        section_match = SECTION_START_RE.match(line)
        if section_match:
            current_type = "section"
            current_record_id = section_match.group(1)
            last_section_id = current_record_id
            current_counts = [int(section_match.group(2))]
            current_gpa_override = None
            current_instructor_override = None
            continue
        prof_match = SECTION_PROF_RE.match(line)
        if prof_match:
            current_type = "section"
            current_record_id = prof_match.group(1)
            last_section_id = current_record_id
            current_counts = []
            gpa_raw = prof_match.group(2)
            current_gpa_override = 0.0 if gpa_raw == "Error" else float(gpa_raw)
            tail = prof_match.group(3).strip()
            first_digit = re.search(r"\d", tail) if tail else None
            current_instructor_override = (tail[:first_digit.start()].strip() if first_digit else tail) or None
            pending_prof_sections.append(
                {"record_id": current_record_id, "gpa": current_gpa_override, "instructor": current_instructor_override}
            )
            continue
        course_total_match = COURSE_TOTAL_START_RE.match(line)
        if course_total_match:
            current_type = "course_total"
            current_record_id = last_section_id
            current_counts = [int(course_total_match.group(1))]
            current_gpa_override = None
            current_instructor_override = None
            continue
        dept_total_match = DEPT_TOTAL_START_RE.match(line)
        if dept_total_match:
            current_type = "department_total"
            current_record_id = "DEPARTMENT_TOTAL"
            current_counts = [int(dept_total_match.group(1))]
            current_gpa_override = None
            current_instructor_override = None
            continue
        if not current_type or PERCENT_RE.match(line):
            continue
        summary = parse_prof_summary(line)
        if not summary:
            tokens = [int(token) for token in INTS_IN_LINE_RE.findall(line)]
            if tokens:
                current_counts.extend(tokens)
            continue
        while len(current_counts) < 5:
            current_counts.append(0)
        a, b, c, d, f_count = current_counts[:5]
        af_total = summary["af_total"]
        i_count, s_count, u_count, q_count, x_count = summary["i"], summary["s"], summary["u"], summary["q"], summary["x"]
        grand_total = summary["grand_total"]
        if summary["style"] == "no_q_lead":
            a = int(current_counts[0]) if current_counts else af_total
            b = c = d = f_count = 0
            af_total = a
            s_count = max(s_count, sum(int(value) for value in current_counts[1:5]))
        gpa = current_gpa_override if current_gpa_override is not None else (0.0 if summary["gpa_raw"] == "Error" else float(summary["gpa_raw"]))
        instructor = current_instructor_override or summary["instructor"]
        if current_type != "section":
            instructor = None
        page_records.append(
            build_record(
                current_type,
                current_record_id,
                a,
                b,
                c,
                d,
                f_count,
                af_total,
                i_count,
                s_count,
                u_count,
                q_count,
                x_count,
                grand_total,
                gpa,
                instructor,
                record_index,
            )
        )
        record_index += 1
        if current_type == "course_total" and len(pending_prof_sections) == 1:
            section = pending_prof_sections[0]
            page_records.append(
                build_record(
                    "section",
                    section["record_id"],
                    a,
                    b,
                    c,
                    d,
                    f_count,
                    af_total,
                    i_count,
                    s_count,
                    u_count,
                    q_count,
                    x_count,
                    grand_total,
                    section["gpa"] if section["gpa"] is not None else gpa,
                    section["instructor"],
                    record_index,
                )
            )
            record_index += 1
        if current_type in {"course_total", "department_total"}:
            pending_prof_sections = []
        current_type = ""
        current_record_id = ""; current_counts = []; current_gpa_override = None; current_instructor_override = None
    return page_records
