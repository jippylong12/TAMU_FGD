# Refactored Workflow (Python Orchestration)

## Goal
Keep orchestration explicit and maintainable:
- Root directory stays clean.
- Modules are grouped by responsibility.
- Entry points are predictable.

## Folder Structure
- `main.py`
  - Thin root entrypoint.
- `scripts/`
  - Standalone utility entrypoints for download checks.
- `src/tamu_fgd/workflow/`
  - `models.py` for typed config and term logic.
  - `downloader.py` for HTTP download class.
  - `runner.py` for stage orchestration.
- `src/tamu_fgd/legacy/`
  - Existing parser/transform/master-db modules retained.
- `src/tamu_fgd/tools/`
  - Utility download scripts as importable modules.

## Typical Commands
Run full workflow for Fall 2023:

```bash
python3 main.py --mode full --years 2023 --semesters FALL --insecure
```

Download-only smoke check (HTTP):

```bash
python3 scripts/download_pdfs_http.py --year 2023 --semester FALL --colleges EN --insecure
```

Download-only smoke check (Selenium):

```bash
python3 scripts/download_pdfs_selenium4.py --year 2023 --semester FALL --colleges EN --headless
```

Parse existing PDFs only:

```bash
python3 main.py --mode parse --years 2023 --semesters FALL
```

Override college list:

```bash
python3 main.py --mode full --years 2023 --semesters FALL --colleges EN,BA,AT --insecure
```

## Notes
- Default college codes are term-aware:
  - pre-Fall-2022: legacy list
  - Fall-2022 and later: modern working list
- `--insecure` exists for environments with certificate-chain interception.
