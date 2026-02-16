import ssl
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from tamu_fgd.workflow.models import TermSpec

BASE_URL = "https://web-as.tamu.edu/GradeReports/PDFReports"


@dataclass(frozen=True)
class DownloadSummary:
    downloaded: list[str]
    failed: list[str]


class HttpGradeReportDownloader:
    def __init__(self, download_root: Path, timeout_seconds: int, insecure_tls: bool) -> None:
        self.download_root = download_root
        self.timeout_seconds = timeout_seconds
        self.ssl_context = ssl._create_unverified_context() if insecure_tls else None

    def download_term(self, term: TermSpec, college_codes: list[str]) -> DownloadSummary:
        term_dir = self.download_root / term.folder_name
        term_dir.mkdir(parents=True, exist_ok=True)
        downloaded = []
        failed = []

        print(f"[DOWNLOAD] Saving to {term_dir}")
        for code in college_codes:
            filename = self._build_filename(term, code)
            url = f"{BASE_URL}/{term.report_key}/{filename}"
            output_path = term_dir / filename
            ok = self._download_pdf(url=url, output_path=output_path, code=code, filename=filename)
            if ok:
                downloaded.append(code)
            else:
                failed.append(code)
        return DownloadSummary(downloaded=downloaded, failed=failed)

    @staticmethod
    def _build_filename(term: TermSpec, college_code: str) -> str:
        return f"grd{term.report_key}{college_code}.pdf"

    def _download_pdf(self, url: str, output_path: Path, code: str, filename: str) -> bool:
        try:
            with urlopen(url, timeout=self.timeout_seconds, context=self.ssl_context) as response:
                status = getattr(response, "status", 200)
                content_type = response.headers.get("Content-Type", "")
                if status != 200:
                    print(f"[DOWNLOAD][FAIL] {code} ({filename}): HTTP {status}")
                    return False
                if "pdf" not in content_type.lower():
                    print(f"[DOWNLOAD][FAIL] {code} ({filename}): Unexpected type {content_type}")
                    return False
                output_path.write_bytes(response.read())
                print(f"[DOWNLOAD][OK] {code} ({filename})")
                return True
        except HTTPError as exc:
            print(f"[DOWNLOAD][FAIL] {code} ({filename}): HTTP {exc.code}")
            return False
        except URLError as exc:
            print(f"[DOWNLOAD][FAIL] {code} ({filename}): {exc.reason}")
            return False
        except TimeoutError:
            print(f"[DOWNLOAD][FAIL] {code} ({filename}): timeout")
            return False
