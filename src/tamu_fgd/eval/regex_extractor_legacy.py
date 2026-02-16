import re
from collections import defaultdict

from pypdf import PdfReader

from tamu_fgd.eval.regex_extractor_standard import build_record

SECTION_WITH_GPA_RE = re.compile(
    r"^([A-Z]{2,8}-\d{3,4}-[A-Z0-9]{2,4})\s+((?:Error)|(?:\d+(?:\.\d+)?))\s*(.*)$"
)
INTS_IN_LINE_RE = re.compile(r"\d+")


def parse_legacy_section(line: str) -> dict | None:
    match = SECTION_WITH_GPA_RE.match(line)
    if not match:
        return None
    return {
        "record_id": match.group(1),
        "gpa_raw": match.group(2),
        "instructor": match.group(3).strip() or None,
    }


def parse_legacy_counts(line: str) -> list[int] | None:
    values = [int(token) for token in INTS_IN_LINE_RE.findall(line)]
    if len(values) != 12:
        return None
    return values


def parse_legacy_pdf(reader: PdfReader) -> dict[str, list[dict]]:
    pages_payload: dict[str, list[dict]] = {
        str(page_number): [] for page_number in range(1, len(reader.pages) + 1)
    }
    record_index_by_page: defaultdict[int, int] = defaultdict(int)
    started = False
    pending: dict | None = None

    for page_number, page in enumerate(reader.pages, start=1):
        lines = [line.rstrip() for line in (page.extract_text() or "").splitlines() if line.strip()]
        for line in lines:
            if not started:
                if "GRADE DISTRIBUTION REPORT" in line.upper():
                    started = True
                continue

            section = parse_legacy_section(line)
            if section:
                pending = {
                    "page_number": page_number,
                    "record_id": section["record_id"],
                    "gpa_raw": section["gpa_raw"],
                    "instructor": section["instructor"],
                }
                continue

            if not pending:
                continue

            counts = parse_legacy_counts(line)
            if counts is None:
                continue

            a, b, c, d, f_count = counts[:5]
            af_total = counts[5]
            i_count, s_count, u_count, q_count, x_count = counts[6:11]
            grand_total = counts[11]
            gpa = 0.0 if pending["gpa_raw"] == "Error" else float(pending["gpa_raw"])
            target_page = pending["page_number"]
            record_index = record_index_by_page[target_page]

            pages_payload[str(target_page)].append(
                build_record(
                    "section",
                    pending["record_id"],
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
                    pending["instructor"],
                    record_index,
                )
            )
            record_index_by_page[target_page] += 1
            pending = None

    return pages_payload
