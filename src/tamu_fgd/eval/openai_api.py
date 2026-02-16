import json
import os
import ssl
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_BASE = "https://api.openai.com/v1"

try:
    import certifi
except ImportError:
    certifi = None


class OpenAIHttpClient:
    def __init__(self, api_key: str, timeout_seconds: int = 120, verbose: bool = False) -> None:
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.verbose = verbose
        self.ssl_context = self._build_ssl_context()

    def create_chat_completion(self, payload: dict) -> dict:
        return self.request_json("POST", "/chat/completions", payload)

    def create_file(self, file_path: Path, purpose: str = "batch") -> dict:
        boundary = f"----codex-{uuid.uuid4().hex}"
        file_bytes = file_path.read_bytes()
        parts = [
            f"--{boundary}\r\n"
            "Content-Disposition: form-data; name=\"purpose\"\r\n\r\n"
            f"{purpose}\r\n",
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"file\"; filename=\"{file_path.name}\"\r\n"
            "Content-Type: application/jsonl\r\n\r\n",
        ]
        body = "".join(parts).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        return self.request_json("POST", "/files", None, raw_body=body, extra_headers=headers)

    def create_batch(self, input_file_id: str, metadata: dict | None = None) -> dict:
        payload = {
            "input_file_id": input_file_id,
            "endpoint": "/v1/chat/completions",
            "completion_window": "24h",
        }
        if metadata:
            payload["metadata"] = metadata
        return self.request_json("POST", "/batches", payload)

    def retrieve_batch(self, batch_id: str) -> dict:
        return self.request_json("GET", f"/batches/{batch_id}", None)

    def download_file_content(self, file_id: str) -> bytes:
        return self.request_bytes("GET", f"/files/{file_id}/content")

    def request_json(
        self,
        method: str,
        path: str,
        payload: dict | None,
        raw_body: bytes | None = None,
        extra_headers: dict | None = None,
    ) -> dict:
        data = raw_body if raw_body is not None else (json.dumps(payload).encode("utf-8") if payload else None)
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if raw_body is None:
            headers["Content-Type"] = "application/json"
        if extra_headers:
            headers.update(extra_headers)
        response = self._request_with_retries(method, path, data, headers)
        return json.loads(response.decode("utf-8"))

    def request_bytes(self, method: str, path: str) -> bytes:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return self._request_with_retries(method, path, None, headers)

    def _request_with_retries(
        self,
        method: str,
        path: str,
        data: bytes | None,
        headers: dict,
        max_attempts: int = 4,
    ) -> bytes:
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                request = Request(f"{API_BASE}{path}", data=data, headers=headers, method=method)
                with urlopen(request, timeout=self.timeout_seconds, context=self.ssl_context) as response:
                    return response.read()
            except HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                is_retryable = exc.code in (429, 500, 502, 503, 504)
                last_error = RuntimeError(f"HTTP {exc.code} on {path}: {body}")
                if attempt < max_attempts and is_retryable:
                    self._sleep_backoff(attempt, path, exc.code)
                    continue
                raise last_error
            except URLError as exc:
                last_error = RuntimeError(f"Network error on {path}: {exc.reason}")
                if attempt < max_attempts:
                    self._sleep_backoff(attempt, path, "network")
                    continue
                raise last_error
        if last_error is not None:
            raise last_error
        raise RuntimeError(f"Request failed for {path}")

    def _sleep_backoff(self, attempt: int, path: str, reason) -> None:
        delay = min(10, attempt * 2)
        if self.verbose:
            print(f"[OPENAI][RETRY] {path} reason={reason} sleeping={delay}s")
        time.sleep(delay)

    def _build_ssl_context(self) -> ssl.SSLContext:
        if os.getenv("OPENAI_INSECURE_SKIP_VERIFY") == "1":
            if self.verbose:
                print("[OPENAI][WARN] SSL verification disabled via OPENAI_INSECURE_SKIP_VERIFY=1")
            return ssl._create_unverified_context()

        cafile = os.getenv("OPENAI_SSL_CERT_FILE") or os.getenv("SSL_CERT_FILE")
        if not cafile and certifi is not None:
            cafile = certifi.where()
        if cafile and Path(cafile).exists():
            if self.verbose:
                print(f"[OPENAI] Using SSL CA bundle: {cafile}")
            return ssl.create_default_context(cafile=cafile)
        return ssl.create_default_context()
