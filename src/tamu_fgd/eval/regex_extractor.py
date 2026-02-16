from pathlib import Path

from pypdf import PdfReader

from tamu_fgd.eval.regex_extractor_prof import parse_prof_page
from tamu_fgd.eval.regex_extractor_standard import parse_standard_page


def parse_pdf(pdf_path: Path) -> dict[str, list[dict]]:
    reader = PdfReader(str(pdf_path))
    is_prof = "_PROF" in pdf_path.name.upper()
    page_parser = parse_prof_page if is_prof else parse_standard_page
    pages_payload: dict[str, list[dict]] = {}
    for page_number, page in enumerate(reader.pages, start=1):
        lines = [line.rstrip() for line in (page.extract_text() or "").splitlines() if line.strip()]
        pages_payload[str(page_number)] = page_parser(lines)
    return pages_payload
