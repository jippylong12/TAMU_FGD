from tamu_fgd.eval.schema import PAGE_RECORDS_SCHEMA

SYSTEM_PROMPT = (
    "Extract grade distribution rows from one TAMU page. "
    "Return records in the same top-to-bottom order as the page. "
    "Use record_type values: section, course_total, department_total. "
    "For missing numeric fields, use 0. For missing instructor, use null."
)


def build_chat_body(model: str, page_idx: int, page_text: str) -> dict:
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Page number: {page_idx}\n"
                    "Extract records from this page text:\n"
                    f"{page_text}"
                ),
            },
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "tamu_page_records",
                "strict": True,
                "schema": PAGE_RECORDS_SCHEMA,
            },
        },
    }
