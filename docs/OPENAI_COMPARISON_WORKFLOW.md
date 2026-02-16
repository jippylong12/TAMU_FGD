# OpenAI Extraction Workflow (Single College)

## Goal
Extract one Fall 2023 PDF into structured JSON using OpenAI only.

## Target JSON Shape
The output JSON files use this root shape:
- root object keys are page numbers (`"1"`, `"2"`, ...)
- each page value is an ordered array of records

Each record includes:
- `record_index` (order on page)
- `record_type` (`section`, `course_total`, `department_total`)
- `record_id`
- `counts` (`a`, `b`, `c`, `d`, `f`, `af_total`, `i`, `s`, `u`, `q`, `x`, `grand_total`)
- `gpa`
- `instructor` (`string` or `null`)

## Run Command
From `TAMU_FGD/`:

```bash
python3 scripts/evaluate_openai_vs_legacy.py \
  --pdf GradeDistributionsDB/Fall2023/grd20233EN.pdf \
  --output-dir eval_output/en_fall2023 \
  --model gpt-4.1-mini
```

Batch-first flow for large PDFs:

```bash
OPENAI_MODE=batch-submit bash scripts/run_openai_comparison.sh
OPENAI_MODE=batch-wait bash scripts/run_openai_comparison.sh
```

## Outputs
- `openai.json`
- `openai_summary.json`
- `batch_errors.json` (when batch mode is used)

All under your `--output-dir`.

## Notes
- `OPENAI_API_KEY` must be set for extraction.
- Batch mode writes durable state and raw batch artifacts in `<output_dir>/batch_state/`.
- `openai_summary.json` includes page and record totals plus record-type breakdown.
