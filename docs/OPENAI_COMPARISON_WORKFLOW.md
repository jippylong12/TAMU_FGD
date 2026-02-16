# OpenAI vs Legacy Comparison (Single College)

## Goal
Compare one Fall 2023 PDF parsed by:
- legacy extractor
- OpenAI extractor

## Target JSON Shape
The output JSON files use this root shape:
- root object keys are page numbers (`"1"`, `"2"`, ...)
- each page value is an ordered array of records

Each record includes:
- `record_index` (order on page)
- `record_type` (`section`, `course_total`, `department_total`)
- `record_id`
- `counts` (`a`, `b`, `c`, `d`, `f`, `af_total`, `i`, `s`, `u`, `q`, `x`, `isuqx_total`)
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

If you only want legacy JSON without OpenAI calls:

```bash
python3 scripts/evaluate_openai_vs_legacy.py \
  --pdf GradeDistributionsDB/Fall2023/grd20233EN.pdf \
  --output-dir eval_output/en_fall2023 \
  --skip-openai
```

## Outputs
- `legacy.json`
- `openai.json`
- `comparison.json`

All under your `--output-dir`.

## Notes
- `OPENAI_API_KEY` must be set for OpenAI extraction.
- Comparison currently focuses on `section` records and preserves on-page order.
