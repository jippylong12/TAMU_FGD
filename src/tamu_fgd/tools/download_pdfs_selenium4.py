#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
from typing import List

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from tamu_fgd.tools.selenium_support import (
    align_driver_path_with_chrome,
    available_college_values,
    select_college,
    select_year_semester,
    setup_driver,
    wait_for_pdf,
)

BASE_URL = "https://web-as.tamu.edu/gradereports/"
DOWNLOAD_BUTTON_ID = "ctl00_plcMain_btnGrade"

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
        description="Download TAMU grade distribution PDFs using Selenium 4."
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
        default=60,
        help="Max wait per PDF download.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome in headless mode.",
    )
    parser.add_argument(
        "--chromedriver-path",
        type=str,
        default="",
        help="Optional explicit chromedriver binary path.",
    )
    return parser.parse_args()


def parse_college_codes(raw: str) -> List[str]:
    return [code.strip() for code in raw.split(",") if code.strip()]


def main() -> int:
    args = parse_args()
    semester = args.semester.upper()
    colleges = parse_college_codes(args.colleges)
    if not colleges:
        print("No colleges provided.")
        return 1

    if semester not in SEMESTER_TO_TERM_NUMBER:
        print(f"Unsupported semester: {semester}")
        return 1

    term_folder = f"{SEMESTER_TO_FOLDER[semester]}{args.year}"
    download_dir = Path(args.download_root).resolve() / term_folder
    download_dir.mkdir(parents=True, exist_ok=True)

    print(f"Download directory: {download_dir}")
    print(f"Target term: {semester} {args.year}")
    print(f"College codes: {', '.join(colleges)}")

    align_driver_path_with_chrome()
    driver = setup_driver(
        download_dir=download_dir,
        headless=args.headless,
        chromedriver_path=args.chromedriver_path,
    )
    wait = WebDriverWait(driver, 20)

    downloaded = []
    failed = []
    term_num = SEMESTER_TO_TERM_NUMBER[semester]

    try:
        for college in colleges:
            try:
                driver.get(BASE_URL)
                select_year_semester(driver, args.year, semester, wait)
                if not select_college(driver, college):
                    choices = ", ".join(sorted(set(available_college_values(driver))))
                    print(f"[SKIP] College value '{college}' not found. Available values: {choices}")
                    failed.append(college)
                    continue

                expected_name = f"grd{args.year}{term_num}{college}.pdf"
                expected_path = download_dir / expected_name
                if expected_path.exists():
                    os.remove(expected_path)

                button = driver.find_element(By.ID, DOWNLOAD_BUTTON_ID)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                try:
                    button.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", button)

                result = wait_for_pdf(
                    download_dir=download_dir,
                    expected_file_name=expected_name,
                    timeout_seconds=args.timeout_seconds,
                )
                if result is None:
                    print(f"[FAIL] Timed out waiting for {expected_name}")
                    failed.append(college)
                else:
                    print(f"[OK] Downloaded {result.name}")
                    downloaded.append(college)
            except (TimeoutException, WebDriverException) as exc:
                print(f"[FAIL] {college}: {exc.__class__.__name__}")
                failed.append(college)
    except TimeoutException as exc:
        print(f"[ERROR] Timed out loading form controls: {exc}")
        return 1
    finally:
        driver.quit()

    print("")
    print(f"Downloaded: {len(downloaded)}")
    print(f"Failed: {len(failed)}")
    if failed:
        print(f"Failed colleges: {', '.join(failed)}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
