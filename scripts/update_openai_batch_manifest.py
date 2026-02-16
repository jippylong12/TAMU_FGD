#!/usr/bin/env python3
import argparse
import glob
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

TERMINAL_FAILED = {"failed", "expired", "cancelled"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build batch manifest JSON for semester OpenAI runs.")
    parser.add_argument("--pdf-glob", required=True, help="Glob used for semester PDF inputs.")
    parser.add_argument("--output-root", required=True, help="Root folder containing per-college outputs.")
    parser.add_argument("--term-key", required=True, help="Term key prefix used in filenames (example: 20233).")
    parser.add_argument("--label", required=True, help="Semester label suffix used in output folders.")
    parser.add_argument("--manifest-path", required=True, help="Output manifest JSON path.")
    parser.add_argument("--mode", required=True, help="Current runner mode.")
    parser.add_argument("--semester", required=True, help="Semester season name.")
    parser.add_argument("--year", required=True, help="Semester year.")
    return parser


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def code_from_pdf(pdf_name: str, term_key: str) -> str:
    if not pdf_name.startswith(f"grd{term_key}") or not pdf_name.endswith(".pdf"):
        return ""
    return pdf_name[len(f"grd{term_key}") : -4]


def classify_state(openai_exists: bool, status: str, has_state: bool) -> str:
    if openai_exists:
        return "done"
    if status in TERMINAL_FAILED:
        return "failed"
    if status == "completed":
        return "ready_to_collect"
    if has_state:
        return "in_progress"
    return "pending"


def main() -> int:
    args = build_parser().parse_args()
    output_root = Path(args.output_root).resolve()
    manifest_path = Path(args.manifest_path).resolve()
    pdf_paths = sorted(Path(p).resolve() for p in glob.glob(args.pdf_glob))

    entries = []
    for pdf_path in pdf_paths:
        code = code_from_pdf(pdf_path.name, args.term_key)
        if not code:
            continue
        output_dir = output_root / f"{code.lower()}_{args.label}"
        batch_state_path = output_dir / "batch_state" / "batch_state.json"
        batch_status_path = output_dir / "batch_status.json"
        openai_path = output_dir / "openai.json"
        state_obj = read_json(batch_state_path)
        status_obj = read_json(batch_status_path)
        status = status_obj.get("status", "")
        entry_state = classify_state(
            openai_exists=openai_path.exists() and openai_path.stat().st_size > 0,
            status=status,
            has_state=batch_state_path.exists(),
        )
        entries.append(
            {
                "code": code,
                "pdf_path": str(pdf_path),
                "output_dir": str(output_dir),
                "state": entry_state,
                "openai_exists": openai_path.exists() and openai_path.stat().st_size > 0,
                "batch_id": state_obj.get("batch_id"),
                "batch_status": status,
                "request_counts": status_obj.get("request_counts") or {},
            }
        )

    counts = Counter(item["state"] for item in entries)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "semester": args.semester,
        "year": args.year,
        "term_key": args.term_key,
        "label": args.label,
        "output_root": str(output_root),
        "counts": {
            "total": len(entries),
            "done": counts.get("done", 0),
            "ready_to_collect": counts.get("ready_to_collect", 0),
            "in_progress": counts.get("in_progress", 0),
            "pending": counts.get("pending", 0),
            "failed": counts.get("failed", 0),
            "remaining": counts.get("ready_to_collect", 0) + counts.get("in_progress", 0) + counts.get("pending", 0),
        },
        "entries": entries,
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(
        "[MANIFEST] "
        f"path={manifest_path} total={payload['counts']['total']} "
        f"done={payload['counts']['done']} remaining={payload['counts']['remaining']} "
        f"failed={payload['counts']['failed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
