#!/usr/bin/env python3
import argparse
from typing import Optional

from tamu_fgd.workflow.models import WorkflowConfig, parse_csv_arg, parse_terms
from tamu_fgd.workflow.runner import GradeDistributionWorkflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run TAMU grade-distribution workflow with explicit stages."
    )
    parser.add_argument(
        "--mode",
        choices=("download", "parse", "full"),
        default="full",
        help="download: fetch PDFs only, parse: parse existing PDFs only, full: download then parse.",
    )
    parser.add_argument(
        "--years",
        required=True,
        help="Comma-separated years (example: 2023 or 2022,2023).",
    )
    parser.add_argument(
        "--semesters",
        default="FALL",
        help="Comma-separated semesters (SPRING,SUMMER,FALL or A,B,C).",
    )
    parser.add_argument(
        "--colleges",
        default="",
        help="Optional comma-separated college code override.",
    )
    parser.add_argument(
        "--download-root",
        default="GradeDistributionsDB",
        help="Root directory for downloaded/parsed term folders.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=45,
        help="Per-file download timeout in seconds.",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification for download requests.",
    )
    parser.add_argument(
        "--skip-master-db",
        action="store_true",
        help="Skip createMasterDB/create_courses_lists after parse mode.",
    )
    return parser


def parse_college_override(raw: str) -> Optional[list[str]]:
    codes = parse_csv_arg(raw)
    return codes if codes else None


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        terms = parse_terms(args.years, args.semesters)
    except ValueError as exc:
        parser.error(str(exc))
        return

    config = WorkflowConfig(
        mode=args.mode,
        terms=terms,
        college_codes=parse_college_override(args.colleges),
        download_root=args.download_root,
        timeout_seconds=args.timeout_seconds,
        insecure_tls=args.insecure,
        skip_master_db=args.skip_master_db,
    )
    GradeDistributionWorkflow(config=config).run()
