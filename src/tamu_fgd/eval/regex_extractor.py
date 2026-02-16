import re
from pathlib import Path

from pypdf import PdfReader

from tamu_fgd.eval.regex_extractor_legacy import parse_legacy_pdf
from tamu_fgd.eval.regex_extractor_prof import parse_prof_page
from tamu_fgd.eval.regex_extractor_standard import parse_standard_page

TERM_KEY_RE = re.compile(r"^grd(\d{4})([123])", re.IGNORECASE)


def extract_term_from_filename(pdf_path: Path) -> tuple[int, int] | None:
    match = TERM_KEY_RE.match(pdf_path.stem)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def is_legacy_term(year: int, term_digit: int) -> bool:
    if year < 2016:
        return True
    return year == 2016 and term_digit < 3


def parser_mode(pdf_path: Path) -> str:
    term = extract_term_from_filename(pdf_path)
    if term is not None and is_legacy_term(term[0], term[1]):
        return "legacy"
    if "_PROF" in pdf_path.name.upper():
        return "modern_prof"
    return "modern"


def parse_pdf(pdf_path: Path) -> dict[str, list[dict]]:
    reader = PdfReader(str(pdf_path))
    mode = parser_mode(pdf_path)
    if mode == "legacy":
        return parse_legacy_pdf(reader)

    page_parser = parse_prof_page if mode == "modern_prof" else parse_standard_page
    pages_payload: dict[str, list[dict]] = {}
    for page_number, page in enumerate(reader.pages, start=1):
        lines = [line.rstrip() for line in (page.extract_text() or "").splitlines() if line.strip()]
        pages_payload[str(page_number)] = page_parser(lines)
    return pages_payload
