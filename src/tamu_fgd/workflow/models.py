from dataclasses import dataclass
from typing import Optional

SEMESTER_ORDER = ("SPRING", "SUMMER", "FALL")
SEMESTER_METADATA = {
    "SPRING": {"title": "Spring", "legacy_code": "A", "term_number": "1"},
    "SUMMER": {"title": "Summer", "legacy_code": "B", "term_number": "2"},
    "FALL": {"title": "Fall", "legacy_code": "C", "term_number": "3"},
}
SEMESTER_ALIASES = {"A": "SPRING", "B": "SUMMER", "C": "FALL"}

LEGACY_COLLEGE_CODES = [
    "AE", "AC", "AG", "AR", "AP", "AT", "BA", "DN", "DN_PROF", "DT",
    "DT_PROF", "ED", "EN", "GB", "GE", "SL", "SL_PROF", "LA", "MD", "MD_PROF",
    "MN", "MN_PROF", "MS", "NS", "CP_PROF", "PM_PROF", "PH", "SC", "VF",
    "VM", "VM_PROF", "VT", "VT_PROF",
]
POST_FALL_2022_CODES = [
    "AC", "AE", "AG", "AP", "AT", "BA", "DT", "DT_PROF", "EH", "EN", "GB",
    "GV", "MN", "MS", "NS", "PH", "PM_PROF", "QT", "SL", "SL_PROF", "VF",
    "VT", "VT_PROF",
]


@dataclass(frozen=True)
class TermSpec:
    year: int
    semester_key: str

    def __post_init__(self) -> None:
        if self.semester_key not in SEMESTER_METADATA:
            raise ValueError(f"Unsupported semester key: {self.semester_key}")

    @property
    def title(self) -> str:
        return SEMESTER_METADATA[self.semester_key]["title"]

    @property
    def term_number(self) -> str:
        return SEMESTER_METADATA[self.semester_key]["term_number"]

    @property
    def folder_name(self) -> str:
        return f"{self.title}{self.year}"

    @property
    def report_key(self) -> str:
        return f"{self.year}{self.term_number}"


@dataclass(frozen=True)
class WorkflowConfig:
    mode: str
    terms: list[TermSpec]
    college_codes: Optional[list[str]]
    download_root: str
    timeout_seconds: int
    insecure_tls: bool
    skip_master_db: bool


def parse_csv_arg(raw: str) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def normalize_semester(raw: str) -> str:
    key = raw.strip().upper()
    if key in SEMESTER_METADATA:
        return key
    if key in SEMESTER_ALIASES:
        return SEMESTER_ALIASES[key]
    raise ValueError(f"Unsupported semester value: {raw}")


def parse_terms(years_arg: str, semesters_arg: str) -> list[TermSpec]:
    years = []
    for raw_year in parse_csv_arg(years_arg):
        try:
            years.append(int(raw_year))
        except ValueError as exc:
            raise ValueError(f"Invalid year value: {raw_year}") from exc
    if not years:
        raise ValueError("At least one year is required.")

    raw_semesters = parse_csv_arg(semesters_arg) or ["FALL"]
    semester_keys = [normalize_semester(item) for item in raw_semesters]
    terms = [TermSpec(year=year, semester_key=semester) for year in years for semester in semester_keys]
    terms.sort(key=lambda term: (term.year, SEMESTER_ORDER.index(term.semester_key)))
    return terms


def is_post_fall_2022(term: TermSpec) -> bool:
    if term.year > 2022:
        return True
    return term.year == 2022 and term.semester_key == "FALL"


def default_college_codes(term: TermSpec) -> list[str]:
    if is_post_fall_2022(term):
        return POST_FALL_2022_CODES.copy()
    return LEGACY_COLLEGE_CODES.copy()


def resolve_college_codes(term: TermSpec, override: Optional[list[str]]) -> list[str]:
    if override:
        return override.copy()
    return default_college_codes(term)
