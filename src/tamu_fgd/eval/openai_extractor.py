import json
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen

from pypdf import PdfReader

from tamu_fgd.eval.schema import PAGE_RECORDS_SCHEMA

API_URL = "https://api.openai.com/v1/chat/completions"
SYSTEM_PROMPT = (
    "Extract grade distribution rows from one TAMU page. "
    "Return records in the same top-to-bottom order as the page. "
    "Use record_type values: section, course_total, department_total. "
    "For missing numeric fields, use 0. For missing instructor, use null."
)


class OpenAIPageExtractor:
    def __init__(self, api_key: str, model: str, timeout_seconds: int = 120, verbose: bool = False) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.verbose = verbose

    def extract(self, pdf_path: Path, max_pages: Optional[int] = None) -> dict:
        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)
        if max_pages is not None:
            total_pages = min(total_pages, max_pages)
        result = {}
        if self.verbose:
            print(f"[OPENAI] Extracting {total_pages} page(s) from {pdf_path.name}")
        for page_idx, page in enumerate(reader.pages, start=1):
            if max_pages is not None and page_idx > max_pages:
                break
            if self.verbose:
                print(f"[OPENAI] Page {page_idx}/{total_pages}: reading text")
            page_text = page.extract_text() or ""
            if self.verbose:
                print(f"[OPENAI] Page {page_idx}/{total_pages}: requesting structured extraction")
            records = self._extract_page_records(page_idx=page_idx, page_text=page_text)
            for index, record in enumerate(records):
                record["record_index"] = index
            result[str(page_idx)] = records
            if self.verbose:
                print(f"[OPENAI] Page {page_idx}/{total_pages}: received {len(records)} record(s)")
        return result

    def _extract_page_records(self, page_idx: int, page_text: str) -> list[dict]:
        payload = {
            "model": self.model,
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
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            API_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            raw = json.loads(response.read().decode("utf-8"))
        if self.verbose and "usage" in raw:
            usage = raw["usage"]
            print(
                "[OPENAI] "
                f"Page {page_idx}: tokens prompt={usage.get('prompt_tokens')} "
                f"completion={usage.get('completion_tokens')} total={usage.get('total_tokens')}"
            )
        content = raw["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return parsed["records"]
