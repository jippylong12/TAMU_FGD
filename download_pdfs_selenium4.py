#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Iterable, List, Optional

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

BASE_URL = "https://web-as.tamu.edu/gradereports/"
YEAR_ID = "ctl00_plcMain_lstGradYear"
TERM_ID = "ctl00_plcMain_lstGradTerm"
COLLEGE_ID = "ctl00_plcMain_lstGradCollege"
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


def _major_version_from_version_output(raw: str) -> Optional[str]:
    match = re.search(r"(\d+)\.", raw)
    if match is None:
        return None
    return match.group(1)


def _read_command_output(args: List[str]) -> str:
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
        return (completed.stdout or completed.stderr or "").strip()
    except Exception:
        return ""


def align_driver_path_with_chrome() -> None:
    chromedriver_path = shutil.which("chromedriver")
    if not chromedriver_path:
        return

    chrome_output = _read_command_output(
        ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"]
    )
    driver_output = _read_command_output([chromedriver_path, "--version"])
    chrome_major = _major_version_from_version_output(chrome_output)
    driver_major = _major_version_from_version_output(driver_output)

    if not chrome_major or not driver_major:
        return
    if chrome_major == driver_major:
        return

    driver_dir = str(Path(chromedriver_path).resolve().parent)
    current_path = os.environ.get("PATH", "")
    parts = current_path.split(os.pathsep)
    filtered = [p for p in parts if str(Path(p).resolve()) != driver_dir]
    os.environ["PATH"] = os.pathsep.join(filtered)
    print(
        f"[INFO] Chrome {chrome_major} vs ChromeDriver {driver_major} mismatch. "
        "Removed PATH chromedriver so Selenium Manager can choose a compatible driver."
    )


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


def setup_driver(
    download_dir: Path,
    headless: bool,
    chromedriver_path: str,
) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_experimental_option(
        "prefs",
        {
            "plugins.always_open_pdf_externally": True,
            "download.default_directory": str(download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
        },
    )
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--ignore-certificate-errors")
    if headless:
        options.add_argument("--headless=new")
    if chromedriver_path:
        service = Service(executable_path=chromedriver_path)
    else:
        service = Service()
    return webdriver.Chrome(service=service, options=options)


def select_year_semester(driver: webdriver.Chrome, year: int, semester: str, wait: WebDriverWait) -> None:
    wait.until(EC.presence_of_element_located((By.ID, YEAR_ID)))
    Select(driver.find_element(By.ID, YEAR_ID)).select_by_visible_text(str(year))
    Select(driver.find_element(By.ID, TERM_ID)).select_by_visible_text(semester)


def select_college(driver: webdriver.Chrome, college_code: str) -> bool:
    college_select = Select(driver.find_element(By.ID, COLLEGE_ID))
    try:
        college_select.select_by_value(college_code)
        return True
    except NoSuchElementException:
        return False


def wait_for_pdf(
    download_dir: Path,
    expected_file_name: str,
    timeout_seconds: int,
) -> Optional[Path]:
    target_pdf = download_dir / expected_file_name
    deadline = time.time() + timeout_seconds
    last_size = -1
    stable_checks = 0

    while time.time() < deadline:
        if target_pdf.exists():
            current_size = target_pdf.stat().st_size
            if current_size > 0 and current_size == last_size:
                stable_checks += 1
            else:
                stable_checks = 0
            last_size = current_size
            if stable_checks >= 2:
                return target_pdf
        time.sleep(0.75)

    return None


def available_college_values(driver: webdriver.Chrome) -> Iterable[str]:
    college_select = Select(driver.find_element(By.ID, COLLEGE_ID))
    for option in college_select.options:
        value = option.get_attribute("value") or ""
        if value:
            yield value


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
