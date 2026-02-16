import re
from pathlib import Path
from typing import Optional

from pypdf import PdfReader

from tamu_fgd.eval.schema import empty_counts

PROF_NAME_REGEX = r"[A-Z\- \,\.\']{2,}$"
SECTION_START_RE = re.compile(r"^\w+\-\d+\-\w+\s+\d+")
SECTION_END_RE = re.compile(r"\d\.\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+")
TOTAL_HINT_RE = re.compile(r"TOTAL:")


class LegacyPageExtractor:
    def extract(self, pdf_path: Path, max_pages: Optional[int] = None) -> dict:
        reader = PdfReader(str(pdf_path))
        result = {}
        for page_idx, page in enumerate(reader.pages, start=1):
            if max_pages is not None and page_idx > max_pages:
                break
            text = page.extract_text() or ""
            lines = text.split("\n")
            records = self._extract_page_records(lines)
            for index, record in enumerate(records):
                record["record_index"] = index
            result[str(page_idx)] = records
        return result

    def _extract_page_records(self, lines: list[str]) -> list[dict]:
        records = []
        state = "collect"
        current_data = ""
        for line in lines:
            if state == "collect":
                start_match = SECTION_START_RE.match(line)
                if start_match is not None:
                    state = "add_data"
                    current_data = " ".join(start_match.group().split())
                    continue

                total = self._parse_inline_total(line)
                if total is not None:
                    records.append(total)
                continue

            end_match = SECTION_END_RE.findall(line)
            if len(end_match) == 0:
                unit = re.compile(r"\d+$").findall(line)
                if len(unit) != 0:
                    current_data += (" " + unit[0])
                continue

            last_unit = re.compile(r"\d+\d+\.").findall(line)
            if len(last_unit) == 0:
                state = "collect"
                current_data = ""
                continue

            prof_name = re.compile(PROF_NAME_REGEX).findall(line)
            if len(prof_name) == 0:
                instructor = "NOT LISTED"
            else:
                instructor = prof_name[0].strip()

            current_data += (" " + last_unit[0][:-2])
            current_data += (" " + " ".join(end_match[0].split()))
            current_data += (" " + instructor)

            section_record = self._parse_section_row(current_data)
            if section_record is not None:
                records.append(section_record)
            state = "collect"
            current_data = ""
        return records

    def _parse_section_row(self, row: str) -> Optional[dict]:
        parts = row.split()
        if len(parts) < 14:
            return None
        if not re.match(r"^\w+\-\d+\-\w+$", parts[0]):
            return None
        try:
            counts = {
                "a": int(parts[1]),
                "b": int(parts[2]),
                "c": int(parts[3]),
                "d": int(parts[4]),
                "f": int(parts[5]),
                "af_total": int(parts[6]),
                "i": int(parts[8]),
                "s": int(parts[9]),
                "u": int(parts[10]),
                "q": int(parts[11]),
                "x": int(parts[12]),
                "isuqx_total": int(parts[13]),
            }
            gpa = float(parts[7])
        except ValueError:
            return None
        instructor = " ".join(parts[14:]).strip() if len(parts) > 14 else "NOT LISTED"
        if instructor == "":
            instructor = "NOT LISTED"
        return {
            "record_type": "section",
            "record_id": parts[0],
            "counts": counts,
            "gpa": gpa,
            "instructor": instructor,
        }

    def _parse_inline_total(self, line: str) -> Optional[dict]:
        if TOTAL_HINT_RE.search(line) is None:
            return None
        clean = " ".join(line.strip().split())
        record_type = "department_total" if "DEPARTMENT" in clean or "COLLEGE" in clean else "course_total"
        label_match = re.match(r"^([A-Z&\-\s]+TOTAL:)", clean)
        if label_match is None:
            return None
        label = label_match.group(1).strip()
        numbers = re.findall(r"\d+\.\d+|\d+", clean)
        if len(numbers) < 7:
            return None
        counts = empty_counts()
        try:
            counts["a"] = int(numbers[0])
            counts["b"] = int(numbers[1])
            counts["c"] = int(numbers[2])
            counts["d"] = int(numbers[3])
            counts["f"] = int(numbers[4])
            counts["af_total"] = int(numbers[5])
            gpa = float(numbers[6])
        except ValueError:
            return None
        return {
            "record_type": record_type,
            "record_id": label,
            "counts": counts,
            "gpa": gpa,
            "instructor": None,
        }
