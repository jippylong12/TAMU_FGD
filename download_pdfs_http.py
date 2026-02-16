#!/usr/bin/env python3
import argparse
import ssl
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

BASE_URL = "https://web-as.tamu.edu/GradeReports/PDFReports"

SEMESTER_TO_TERM_NUMBER = {
    "SPRING": "1",
    "SUMMER": "2",
    "FALL": "3",
}

SEMESTER_TO_FOLDER = {
    "SPRING": "Spring",
    "SUMMER": "Summer",
    "FALL": "Fall",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download TAMU grade distribution PDFs via direct HTTP URLs."
    )
    parser.add_argument("--year", type=int, required=True, help="Report year, e.g. 2023")
    parser.add_argument(
        "--semester",
        type=str,
        required=True,
        choices=["SPRING", "SUMMER", "FALL", "Spring", "Summer", "Fall"],
        help="Report semester.",
    )
    parser.add_argument(
        "--colleges",
        type=str,
        required=True,
        help="Comma-separated college codes (example: EN,BA,SC).",
    )
    parser.add_argument(
        "--download-root",
        type=str,
        default="GradeDistributionsDB",
        help="Root directory where term folders are created.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=30,
        help="Per-request timeout.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification (for local/dev smoke checks only).",
    )
    return parser.parse_args()


def parse_college_codes(raw: str):
    return [code.strip() for code in raw.split(",") if code.strip()]


def main() -> int:
    args = parse_args()
    semester = args.semester.upper()
    colleges = parse_college_codes(args.colleges)
    if semester not in SEMESTER_TO_TERM_NUMBER:
        print(f"Unsupported semester: {semester}")
        return 1
    if not colleges:
        print("No colleges provided.")
        return 1

    term_number = SEMESTER_TO_TERM_NUMBER[semester]
    term_key = f"{args.year}{term_number}"
    term_folder = f"{SEMESTER_TO_FOLDER[semester]}{args.year}"
    download_dir = Path(args.download_root).resolve() / term_folder
    download_dir.mkdir(parents=True, exist_ok=True)

    print(f"Download directory: {download_dir}")
    print(f"Target term: {semester} {args.year}")
    print(f"College codes: {', '.join(colleges)}")

    ok = []
    failed = []
    ssl_context = None
    if args.insecure:
        ssl_context = ssl._create_unverified_context()

    for code in colleges:
        filename = f"grd{term_key}{code}.pdf"
        url = f"{BASE_URL}/{term_key}/{filename}"
        output_path = download_dir / filename
        try:
            with urlopen(url, timeout=args.timeout_seconds, context=ssl_context) as response:
                status = getattr(response, "status", 200)
                content_type = response.headers.get("Content-Type", "")
                if status != 200:
                    print(f"[FAIL] {filename}: HTTP {status}")
                    failed.append(code)
                    continue
                if "pdf" not in content_type.lower():
                    print(f"[FAIL] {filename}: unexpected content type '{content_type}'")
                    failed.append(code)
                    continue
                output_path.write_bytes(response.read())
                print(f"[OK] Downloaded {filename}")
                ok.append(code)
        except HTTPError as exc:
            print(f"[FAIL] {filename}: HTTP {exc.code}")
            failed.append(code)
        except URLError as exc:
            print(f"[FAIL] {filename}: network error {exc.reason}")
            failed.append(code)
        except TimeoutError:
            print(f"[FAIL] {filename}: timeout")
            failed.append(code)

    print("")
    print(f"Downloaded: {len(ok)}")
    print(f"Failed: {len(failed)}")
    if failed:
        print(f"Failed colleges: {', '.join(failed)}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
