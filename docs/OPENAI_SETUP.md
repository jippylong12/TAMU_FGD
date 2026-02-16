# Extraction Setup

## Script Overview
- `scripts/run_regex_year_range_to_masterdb.sh`:
  - one-command all-years workflow on existing PDFs (`regex parse -> combined MasterDB.csv`)
- `scripts/run_regex_terms_to_masterdb.sh`:
  - one-command multi-term workflow (`download -> regex parse -> per-term CSV -> final combined MasterDB.csv for frontend`)
- `scripts/run_regex_semester_to_csv.sh`:
  - one-term workflow (`download -> regex parse -> one term CSV`)
- `scripts/run_regex_batches.sh`:
  - parse existing semester PDFs into `regex.json` artifacts only
- `scripts/extract_regex_json.py`:
  - parse one PDF into page-keyed `regex.json`
- `scripts/generate_masterdb_from_eval_root.sh`:
  - build CSV from one eval root (`openai.json` by default, optional `regex.json`)
- `scripts/generate_masterdb_from_openai.py`:
  - low-level CSV builder from explicit JSON file list (`openai.json` or `regex.json`)

## One-time Setup
From `TAMU_FGD/`:

```bash
bash scripts/setup_env.sh
cp .env.example .env
```

Edit `.env` and set:
- `OPENAI_API_KEY`

Optional:
- `OPENAI_MODEL` (defaults to `gpt-4.1-mini`)

## Primary Path: Regex Extraction (No OpenAI Cost)
Run one PDF:

```bash
python3 scripts/extract_regex_json.py \
  --pdf GradeDistributionsDB/Fall2023/grd20233DT.pdf \
  --output eval_output/dt_fall2023/regex.json
```

Run all Fall 2023 PDFs:

```bash
bash scripts/run_regex_batches.sh --semester fall --year 2023
```

This writes:
- `eval_output/fall2023_all_regex/<college>_fall2023/regex.json`

Run a full semester (download PDFs + regex extraction + semester CSV):

```bash
bash scripts/run_regex_semester_to_csv.sh --semester spring --year 2023
bash scripts/run_regex_semester_to_csv.sh --semester summer --year 2023
```

Run multiple terms and produce one final frontend MasterDB in one command:

```bash
bash scripts/run_regex_terms_to_masterdb.sh \
  --term spring:2023 \
  --term summer:2023 \
  --download-insecure
```

Run all terms in a year range (existing PDFs already in `GradeDistributionsDB/*`) and produce one MasterDB:

```bash
bash scripts/run_regex_year_range_to_masterdb.sh \
  --start-year 2012 \
  --end-year 2023 \
  --semesters spring,summer,fall \
  --jobs 6
```

Parser routing is automatic per PDF:
- pre-Fall 2016 -> legacy parser
- Fall 2016+ -> modern parser
- `_PROF` PDFs -> modern no-`Q` parser

Notes:
- `--jobs` controls concurrent term parsing workers before final MasterDB merge.
- The script always waits for all parse jobs to finish, then builds `MasterDB.csv` once.

If your local Python trust store blocks TAMU TLS cert chain resolution, add:

```bash
bash scripts/run_regex_semester_to_csv.sh --semester spring --year 2023 --download-insecure
```

This writes:
- `eval_output/<semester><year>_all_regex/<college>_<semester><year>/regex.json`
- `GradeDistributionsDB/MasterDBs/MasterDB_<semester><year>_regex.csv`

Compare regex outputs to legacy OpenAI outputs on 5 random colleges:

```bash
python3 scripts/compare_regex_vs_openai_semester_sample.py \
  --regex-root eval_output/fall2023_all_regex \
  --openai-root eval_output/fall2023_all \
  --sample-size 5
```

This writes:
- `eval_output/fall2023_all_regex/regex_vs_openai_college_sample.json`

Note:
- In this branch, OpenAI batch flow is kept as a legacy reference path because it is higher cost.

## Legacy Path: OpenAI Extraction
Default target (`Fall2023 EN`):

```bash
bash scripts/run_openai_comparison.sh
```

This runner prints timestamped progress logs and per-page extraction progress.

## Batch Mode (Recommended For Large PDFs)
Submit a batch job:

```bash
OPENAI_MODE=batch-submit bash scripts/run_openai_comparison.sh
```

Wait for completion (polls status and auto-collects on completion):

```bash
OPENAI_MODE=batch-wait bash scripts/run_openai_comparison.sh
```

Collect results later (if already complete):

```bash
OPENAI_MODE=batch-collect bash scripts/run_openai_comparison.sh
```

Optional controls:
- `BATCH_POLL_SECONDS` (default `30`)
- `BATCH_MAX_WAIT_SECONDS` (default `86400`)
- `BATCH_STATE_DIR` (default `<output_dir>/batch_state`)
- `BATCH_ID` (override state file batch id)
- `MAX_PAGES` (limit pages for test runs)

Custom PDF/output:

```bash
bash scripts/run_openai_comparison.sh \
  GradeDistributionsDB/Fall2023/grd20233BA.pdf \
  eval_output/ba_fall2023
```

## Run Any Semester In Batch (One Command)
From `TAMU_FGD/`:

```bash
bash scripts/run_openai_batches.sh --mode full --semester fall --year 2023
```

Supported modes:
- `submit`
- `wait`
- `collect`
- `full` (submit + wait)
- `status`

Defaults:
- infers `term_key` and output label from `--semester` and `--year` (`fall + 2023` -> `20233`, `fall2023`)
- reads `GradeDistributionsDB/<semester>/grd<term_key>*.pdf`
- writes outputs under `eval_output/<semester_label>_all/<college>_<semester_label>`
- skips already-completed outputs (`openai.json` exists) unless `--force-all` is set
- `wait` polls every submitted batch each cycle (not one batch at a time), auto-collects completed ones, and logs remaining counts

If your folder naming is nonstandard, explicit overrides are still supported:

```bash
bash scripts/run_openai_batches.sh \
  --mode full \
  --semester fall \
  --year 2023 \
  --semester-dir MySemesterFolder \
  --term-key 20233 \
  --label customlabel
```

Runner manifest/report:
- `eval_output/<semester_label>_all/batch_manifest.json`
- includes per-college batch id/status plus summary counts (`done`, `in_progress`, `pending`, `failed`, `remaining`)

Legacy convenience wrapper (fixed to Fall 2023) still works:

```bash
bash scripts/run_openai_fall2023_batches.sh full
```

## Legacy OpenAI Outputs
- `openai.json`
- `openai_summary.json`
- `batch_errors.json` (batch modes)

Written under the output directory you pass in.

## Generate `MasterDB.csv` From OpenAI Output
From `TAMU_FGD/`:

```bash
python3 scripts/generate_masterdb_from_openai.py \
  --eval-output eval_output/dt_fall2023 \
  --output-csv GradeDistributionsDB/MasterDBs/MasterDB.csv \
  --frontend-root ../TAMU_FGD_FRONT_END
```

This generates:
- `GradeDistributionsDB/MasterDBs/MasterDB.csv`

And publishes a copy to:
- `../TAMU_FGD_FRONT_END/MasterDBs/MasterDB.csv`

## Generate One MasterDB From All Batch Outputs (One Command)
From `TAMU_FGD/`:

```bash
bash scripts/generate_masterdb_from_eval_root.sh \
  eval_output/fall2023_all \
  GradeDistributionsDB/MasterDBs/MasterDB.csv \
  ../TAMU_FGD_FRONT_END
```

This discovers all `openai.json` files under `eval_output/fall2023_all` and builds one merged `MasterDB.csv`.

To build from regex outputs instead, pass `regex.json` as the 4th argument:

```bash
bash scripts/generate_masterdb_from_eval_root.sh \
  eval_output/spring2023_all_regex \
  GradeDistributionsDB/MasterDBs/MasterDB_spring2023_regex.csv \
  ../TAMU_FGD_FRONT_END \
  regex.json
```

## Generate Frontend MasterDB from `all_terms_regex`
From `TAMU_FGD/`:

```bash
bash scripts/generate_masterdb_from_eval_root.sh \
  eval_output/all_terms_regex \
  GradeDistributionsDB/MasterDBs/MasterDB_all_terms_regex.csv \
  ../TAMU_FGD_FRONT_END \
  regex.json
```

This discovers all `regex.json` files under `eval_output/all_terms_regex`, builds:
- `GradeDistributionsDB/MasterDBs/MasterDB_all_terms_regex.csv`
- `GradeDistributionsDB/MasterDBs/MasterDB.index.json`

and publishes them to frontend:
- `../TAMU_FGD_FRONT_END/MasterDBs/MasterDB.csv`
- `../TAMU_FGD_FRONT_END/MasterDBs/MasterDB.index.json`
