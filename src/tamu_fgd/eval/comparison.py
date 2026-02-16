def _section_records(page_records: list[dict]) -> list[dict]:
    return [record for record in page_records if record.get("record_type") == "section"]


def compare_section_records(legacy: dict, openai: dict, gpa_tolerance: float = 0.01) -> dict:
    pages = sorted(set(legacy.keys()) | set(openai.keys()), key=lambda item: int(item))
    page_reports = {}
    total_compared = 0
    total_matches = 0
    total_mismatches = 0

    for page in pages:
        legacy_page = _section_records(legacy.get(page, []))
        openai_page = _section_records(openai.get(page, []))
        compared = min(len(legacy_page), len(openai_page))
        matches = 0
        mismatches = []

        for index in range(compared):
            left = legacy_page[index]
            right = openai_page[index]
            diffs = []

            if left["record_id"] != right["record_id"]:
                diffs.append("record_id")

            for key in ["a", "b", "c", "d", "f", "af_total", "i", "s", "u", "q", "x", "isuqx_total"]:
                if left["counts"].get(key) != right["counts"].get(key):
                    diffs.append(f"counts.{key}")

            if abs(float(left["gpa"]) - float(right["gpa"])) > gpa_tolerance:
                diffs.append("gpa")

            left_instr = (left.get("instructor") or "").strip()
            right_instr = (right.get("instructor") or "").strip()
            if left_instr != right_instr:
                diffs.append("instructor")

            if len(diffs) == 0:
                matches += 1
            else:
                mismatches.append(
                    {
                        "record_index": index,
                        "legacy_record_id": left["record_id"],
                        "openai_record_id": right["record_id"],
                        "fields": diffs,
                    }
                )

        page_reports[page] = {
            "legacy_section_count": len(legacy_page),
            "openai_section_count": len(openai_page),
            "compared_count": compared,
            "match_count": matches,
            "mismatch_count": len(mismatches),
            "mismatches": mismatches,
            "unpaired_legacy_sections": max(0, len(legacy_page) - compared),
            "unpaired_openai_sections": max(0, len(openai_page) - compared),
        }
        total_compared += compared
        total_matches += matches
        total_mismatches += len(mismatches)

    return {
        "summary": {
            "pages_compared": len(pages),
            "section_records_compared": total_compared,
            "exact_matches": total_matches,
            "mismatches": total_mismatches,
            "match_rate": 0.0 if total_compared == 0 else round(total_matches / total_compared, 4),
        },
        "pages": page_reports,
    }
