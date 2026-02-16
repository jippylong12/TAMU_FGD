import json
from pathlib import Path
from typing import Optional

from pypdf import PdfReader

from tamu_fgd.eval.openai_api import OpenAIHttpClient
from tamu_fgd.eval.prompting import build_chat_body


def derive_honors(record: dict) -> bool:
    if record.get("record_type") != "section":
        return False
    record_id = str(record.get("record_id") or "")
    parts = record_id.split("-")
    if len(parts) < 3:
        return False
    return parts[2].strip().startswith("2")


class OpenAIPageExtractor:
    def __init__(self, api_key: str, model: str, timeout_seconds: int = 120, verbose: bool = False) -> None:
        self.model = model
        self.verbose = verbose
        self.client = OpenAIHttpClient(
            api_key=api_key,
            timeout_seconds=timeout_seconds,
            verbose=verbose,
        )

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
                record["honors"] = derive_honors(record)
            result[str(page_idx)] = records
            if self.verbose:
                print(f"[OPENAI] Page {page_idx}/{total_pages}: received {len(records)} record(s)")
        return result

    def _extract_page_records(self, page_idx: int, page_text: str) -> list[dict]:
        raw = self.client.create_chat_completion(build_chat_body(self.model, page_idx, page_text))
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
