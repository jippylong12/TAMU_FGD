# OpenAI Extraction Setup

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

## Run Extraction
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

## Outputs
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
