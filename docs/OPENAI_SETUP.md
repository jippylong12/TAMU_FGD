# OpenAI Comparison Setup

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

## Run Comparison
Default target (`Fall2023 EN`):

```bash
bash scripts/run_openai_comparison.sh
```

This runner prints timestamped progress logs and per-page extraction progress.

Custom PDF/output:

```bash
bash scripts/run_openai_comparison.sh \
  GradeDistributionsDB/Fall2023/grd20233BA.pdf \
  eval_output/ba_fall2023
```

## Outputs
- `legacy.json`
- `openai.json`
- `comparison.json`

Written under the output directory you pass in.
