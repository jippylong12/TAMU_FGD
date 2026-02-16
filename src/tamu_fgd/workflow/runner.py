import os
from pathlib import Path

from tamu_fgd.legacy.createCoursesLists import create_courses_lists
from tamu_fgd.legacy.createMasterDB import createMasterDBs
from tamu_fgd.legacy.manipulatePDFs import manipulatePdfs
from tamu_fgd.legacy.outputData import outputData
from tamu_fgd.workflow.downloader import HttpGradeReportDownloader
from tamu_fgd.workflow.models import TermSpec, WorkflowConfig, resolve_college_codes


class GradeDistributionWorkflow:
    def __init__(self, config: WorkflowConfig) -> None:
        self.config = config
        self.project_root = Path(__file__).resolve().parents[3]
        self.download_root = (self.project_root / config.download_root).resolve()
        self.generated_college_codes: set[str] = set()
        self.downloader = HttpGradeReportDownloader(
            download_root=self.download_root,
            timeout_seconds=config.timeout_seconds,
            insecure_tls=config.insecure_tls,
        )

    def run(self) -> None:
        print(f"[WORKFLOW] Mode: {self.config.mode}")
        for term in self.config.terms:
            self._run_term(term)

        if self.config.mode in ("parse", "full") and not self.config.skip_master_db:
            self._build_master_outputs()
        print("[WORKFLOW] Complete.")

    def _run_term(self, term: TermSpec) -> None:
        print("")
        print(f"[TERM] {term.title} {term.year}")
        college_codes = resolve_college_codes(term=term, override=self.config.college_codes)
        print(f"[TERM] College codes ({len(college_codes)}): {', '.join(college_codes)}")

        if self.config.mode in ("download", "full"):
            summary = self.downloader.download_term(term=term, college_codes=college_codes)
            print(
                f"[DOWNLOAD] Summary: {len(summary.downloaded)} success, "
                f"{len(summary.failed)} failed"
            )
            if summary.failed:
                print(f"[DOWNLOAD] Failed codes: {', '.join(summary.failed)}")

        if self.config.mode in ("parse", "full"):
            self._parse_term(term=term)

    def _parse_term(self, term: TermSpec) -> None:
        term_dir = self.download_root / term.folder_name
        if not term_dir.exists():
            print(f"[PARSE] Skipped: missing term directory {term_dir}")
            return

        pdf_files = sorted(term_dir.glob("*.pdf"))
        if not pdf_files:
            print(f"[PARSE] Skipped: no PDFs in {term_dir}")
            return

        output_dir = term_dir / "Output"
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"[PARSE] Found {len(pdf_files)} PDF files.")
        for pdf_path in pdf_files:
            college_code = self._college_code_from_filename(pdf_path.name, term)
            title = f"{term.folder_name} {college_code}.xlsx"
            try:
                os.chdir(self.project_root)
                master_dictionary = manipulatePdfs(pdf_path.name, term.title, str(term.year))
                workbook = outputData(master_dictionary, title)
                workbook.save(output_dir / title)
                self.generated_college_codes.add(college_code)
                print(f"[PARSE][OK] {pdf_path.name} -> {title}")
            except Exception as exc:  # legacy parser can throw mixed exception types
                print(f"[PARSE][FAIL] {pdf_path.name}: {exc}")

    def _build_master_outputs(self) -> None:
        configured_codes = set()
        for term in self.config.terms:
            configured_codes.update(resolve_college_codes(term=term, override=self.config.college_codes))
        if self.generated_college_codes:
            all_codes = sorted(self.generated_college_codes)
        else:
            all_codes = sorted(configured_codes)
        if not all_codes:
            print("[MASTER] Skipped: no college codes available.")
            return

        os.chdir(self.project_root)
        print(f"[MASTER] Building MasterDB for {len(all_codes)} college codes.")
        createMasterDBs(all_codes)
        os.chdir(self.project_root)
        create_courses_lists()
        os.chdir(self.project_root)
        print("[MASTER] MasterDB and course lists updated.")

    @staticmethod
    def _college_code_from_filename(filename: str, term: TermSpec) -> str:
        prefix = f"grd{term.report_key}"
        if filename.startswith(prefix) and filename.endswith(".pdf"):
            return filename[len(prefix):-4]
        return filename.replace(".pdf", "")
