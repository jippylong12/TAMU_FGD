#!/usr/bin/env python3
import argparse
import json
import os
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tamu_fgd.eval.openai_api import OpenAIHttpClient
from tamu_fgd.eval.openai_batch import OpenAIBatchRunner
from tamu_fgd.eval.openai_extractor import OpenAIPageExtractor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run OpenAI extraction for one PDF (live or batch)."
    )
    parser.add_argument("--pdf", required=True, help="Path to target PDF.")
    parser.add_argument("--output-dir", default="eval_output", help="Directory for JSON outputs.")
    parser.add_argument("--model", default="gpt-4.1-mini", help="OpenAI model for extraction.")
    parser.add_argument("--max-pages", type=int, default=None, help="Optional page limit.")
    parser.add_argument(
        "--openai-mode",
        choices=["live", "batch-submit", "batch-wait", "batch-collect"],
        default="live",
        help="OpenAI execution mode.",
    )
    parser.add_argument("--batch-id", default="", help="Existing batch id (for wait/collect).")
    parser.add_argument("--batch-state-dir", default="", help="Directory for batch state files.")
    parser.add_argument("--batch-poll-seconds", type=int, default=30, help="Batch poll interval.")
    parser.add_argument("--batch-max-wait-seconds", type=int, default=86400, help="Max wait in batch-wait mode.")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress logs for extraction and API calls.",
    )
    return parser


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def log(enabled: bool, message: str) -> None:
    if enabled:
        print(message)


def summarize_pages(payload: dict) -> tuple[int, int, dict]:
    page_count = len(payload)
    all_records = [record for page in payload.values() for record in page]
    record_count = len(all_records)
    by_type = Counter(record.get("record_type", "unknown") for record in all_records)
    return page_count, record_count, dict(by_type)


def require_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return api_key


def batch_state_dir(args, output_dir: Path) -> Path:
    if args.batch_state_dir:
        return Path(args.batch_state_dir).resolve()
    return output_dir / "batch_state"


def write_openai_outputs(output_dir: Path, openai_pages: dict, mode: str, batch_meta: dict | None, errors: list) -> None:
    openai_path = output_dir / "openai.json"
    write_json(openai_path, openai_pages)
    print(f"[OK] Wrote OpenAI output: {openai_path}")

    page_count, record_count, by_type = summarize_pages(openai_pages)
    summary = {
        "mode": mode,
        "pages": page_count,
        "records": record_count,
        "records_by_type": by_type,
        "error_count": len(errors),
    }
    if batch_meta:
        summary["batch"] = batch_meta
    summary_path = output_dir / "openai_summary.json"
    write_json(summary_path, summary)
    print(f"[OK] Wrote summary output: {summary_path}")

    errors_path = output_dir / "batch_errors.json"
    write_json(errors_path, {"errors": errors})
    if errors:
        print(f"[WARN] Wrote batch errors: {errors_path}")
    print(
        "[SUMMARY] "
        f"pages={page_count} records={record_count} "
        f"types={by_type} errors={len(errors)}"
    )


def main() -> int:
    args = build_parser().parse_args()
    pdf_path = Path(args.pdf).resolve()
    output_dir = Path(args.output_dir).resolve()
    state_dir = batch_state_dir(args, output_dir)
    log(args.verbose, f"[START] pdf={pdf_path}")
    log(args.verbose, f"[START] output_dir={output_dir}")
    log(args.verbose, f"[START] model={args.model}")
    log(args.verbose, f"[START] mode={args.openai_mode}")
    if args.max_pages is not None:
        log(args.verbose, f"[START] max_pages={args.max_pages}")

    try:
        api_key = require_api_key()
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        return 2
    client = OpenAIHttpClient(api_key=api_key, verbose=args.verbose)

    if args.openai_mode == "live":
        openai = OpenAIPageExtractor(
            api_key=api_key,
            model=args.model,
            verbose=args.verbose,
        ).extract(
            pdf_path=pdf_path,
            max_pages=args.max_pages,
        )
        write_openai_outputs(
            output_dir=output_dir,
            openai_pages=openai,
            mode="live",
            batch_meta=None,
            errors=[],
        )
        return 0

    batch = OpenAIBatchRunner(client=client, model=args.model, verbose=args.verbose)
    try:
        if args.openai_mode == "batch-submit":
            state = batch.submit(pdf_path=pdf_path, state_dir=state_dir, max_pages=args.max_pages)
            print(f"[BATCH] Submitted batch id: {state['batch_id']}")
            print(f"[BATCH] State file: {state_dir / 'batch_state.json'}")
            return 0

        batch_id = batch.resolve_batch_id(state_dir=state_dir, batch_id=args.batch_id or None)
        if args.openai_mode == "batch-wait":
            batch_obj = batch.wait_for_terminal(
                batch_id=batch_id,
                poll_seconds=args.batch_poll_seconds,
                max_wait_seconds=args.batch_max_wait_seconds,
            )
            status = batch_obj.get("status")
            print(f"[BATCH] Terminal status: {status}")
            if status != "completed":
                return 3

        collection = batch.collect(batch_id=batch_id, state_dir=state_dir)
        write_openai_outputs(
            output_dir=output_dir,
            openai_pages=collection["openai_pages"],
            mode=args.openai_mode,
            batch_meta={"batch_id": batch_id},
            errors=collection["errors"],
        )
        return 0
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
