import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pypdf import PdfReader

from tamu_fgd.eval.openai_api import OpenAIHttpClient
from tamu_fgd.eval.prompting import build_chat_body

PAGE_ID_RE = re.compile(r"^page\-(\d+)$")
TERMINAL_STATUSES = {"completed", "failed", "expired", "cancelled"}


def derive_honors(record: dict) -> bool:
    if record.get("record_type") != "section":
        return False
    record_id = str(record.get("record_id") or "")
    parts = record_id.split("-")
    if len(parts) < 3:
        return False
    return parts[2].strip().startswith("2")


class OpenAIBatchRunner:
    def __init__(self, client: OpenAIHttpClient, model: str, verbose: bool = False) -> None:
        self.client = client
        self.model = model
        self.verbose = verbose

    def submit(self, pdf_path: Path, state_dir: Path, max_pages: Optional[int] = None) -> dict:
        state_dir.mkdir(parents=True, exist_ok=True)
        pages = self._extract_pages(pdf_path, max_pages)
        requests_path = state_dir / "requests.jsonl"
        self._write_requests_jsonl(requests_path, pages)
        if self.verbose:
            print(f"[BATCH] Wrote request file: {requests_path}")
        file_obj = self.client.create_file(requests_path)
        batch_obj = self.client.create_batch(
            input_file_id=file_obj["id"],
            metadata={"pdf_name": pdf_path.name, "page_count": str(len(pages))},
        )
        state = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "pdf_path": str(pdf_path),
            "model": self.model,
            "max_pages": max_pages,
            "page_count": len(pages),
            "requests_file": str(requests_path),
            "input_file_id": file_obj["id"],
            "batch_id": batch_obj["id"],
        }
        self._write_state(state_dir, state)
        return state

    def resolve_batch_id(self, state_dir: Path, batch_id: Optional[str]) -> str:
        if batch_id:
            return batch_id
        state = self.read_state(state_dir)
        if "batch_id" not in state:
            raise RuntimeError(f"No batch_id found in {state_dir / 'batch_state.json'}")
        return state["batch_id"]

    def wait_for_terminal(self, batch_id: str, poll_seconds: int, max_wait_seconds: int) -> dict:
        start = time.monotonic()
        last_status = None
        sleep_seconds = max(1, poll_seconds)
        while True:
            batch = self.client.retrieve_batch(batch_id)
            status = batch.get("status")
            req = batch.get("request_counts", {})
            if self.verbose:
                elapsed_seconds = int(time.monotonic() - start)
                status_note = "changed" if status != last_status else "unchanged"
                print(
                    "[BATCH] "
                    f"id={batch_id} status={status} "
                    f"total={req.get('total')} completed={req.get('completed')} failed={req.get('failed')} "
                    f"elapsed={elapsed_seconds}s next_poll={sleep_seconds}s ({status_note})"
                )
                last_status = status
            if status in TERMINAL_STATUSES:
                return batch
            if (time.monotonic() - start) > max_wait_seconds:
                raise RuntimeError(f"Timed out waiting for batch {batch_id}")
            time.sleep(sleep_seconds)

    def status(self, batch_id: str) -> dict:
        return self.client.retrieve_batch(batch_id)

    def collect(self, batch_id: str, state_dir: Path) -> dict:
        state_dir.mkdir(parents=True, exist_ok=True)
        batch = self.client.retrieve_batch(batch_id)
        status = batch.get("status")
        if status != "completed":
            raise RuntimeError(f"Batch {batch_id} is not completed (status={status})")

        openai_pages = {}
        errors = []
        output_id = batch.get("output_file_id")
        if output_id:
            raw_output = self.client.download_file_content(output_id)
            (state_dir / "batch_output.jsonl").write_bytes(raw_output)
            for row in self._read_jsonl_bytes(raw_output):
                page_key, records, error = self._parse_output_row(row)
                if error:
                    errors.append(error)
                    continue
                for idx, record in enumerate(records):
                    record["record_index"] = idx
                    record["honors"] = derive_honors(record)
                openai_pages[page_key] = records

        error_id = batch.get("error_file_id")
        if error_id:
            raw_errors = self.client.download_file_content(error_id)
            (state_dir / "batch_errors.jsonl").write_bytes(raw_errors)
            for row in self._read_jsonl_bytes(raw_errors):
                errors.append({"custom_id": row.get("custom_id"), "error": row.get("error")})

        error_payload = {"batch_id": batch_id, "status": status, "errors": errors}
        with open(state_dir / "page_errors.json", "w", encoding="utf-8") as handle:
            json.dump(error_payload, handle, indent=2)
        return {"batch": batch, "openai_pages": openai_pages, "errors": errors}

    def read_state(self, state_dir: Path) -> dict:
        state_path = state_dir / "batch_state.json"
        if not state_path.exists():
            raise RuntimeError(
                "Missing batch state file: "
                f"{state_path}. "
                "Run OPENAI_MODE=batch-submit first for this output directory, "
                "or provide BATCH_ID/--batch-id for an existing batch."
            )
        with open(state_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_state(self, state_dir: Path, payload: dict) -> None:
        with open(state_dir / "batch_state.json", "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def _extract_pages(self, pdf_path: Path, max_pages: Optional[int]) -> dict[int, str]:
        reader = PdfReader(str(pdf_path))
        pages = {}
        for page_idx, page in enumerate(reader.pages, start=1):
            if max_pages is not None and page_idx > max_pages:
                break
            pages[page_idx] = page.extract_text() or ""
        if self.verbose:
            print(f"[BATCH] Prepared {len(pages)} page(s) from {pdf_path.name}")
        return pages

    def _write_requests_jsonl(self, path: Path, pages: dict[int, str]) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            for page_idx, page_text in pages.items():
                body = build_chat_body(self.model, page_idx, page_text)
                row = {
                    "custom_id": f"page-{page_idx}",
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": body,
                }
                handle.write(json.dumps(row) + "\n")

    def _parse_output_row(self, row: dict) -> tuple[str, list, Optional[dict]]:
        custom_id = row.get("custom_id", "")
        page_key = self._page_key_from_custom_id(custom_id)
        try:
            if row.get("error") is not None:
                return page_key, [], {"custom_id": custom_id, "error": row["error"]}
            response = row.get("response") or {}
            if response.get("status_code") != 200:
                return page_key, [], {"custom_id": custom_id, "error": response}
            body = response.get("body") or {}
            message = (((body.get("choices") or [{}])[0]).get("message") or {})
            content = message.get("content", "")
            if isinstance(content, list):
                text_parts = [part.get("text", "") for part in content if isinstance(part, dict)]
                content = "".join(text_parts)
            parsed = json.loads(content)
            return page_key, parsed.get("records", []), None
        except Exception as exc:
            return page_key, [], {"custom_id": custom_id, "error": f"parse_error: {exc}"}

    @staticmethod
    def _page_key_from_custom_id(custom_id: str) -> str:
        match = PAGE_ID_RE.match(custom_id or "")
        if match is None:
            return custom_id or "unknown"
        return str(int(match.group(1)))

    @staticmethod
    def _read_jsonl_bytes(blob: bytes) -> list[dict]:
        rows = []
        for line in blob.decode("utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows
