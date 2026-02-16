#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f ".venv/bin/activate" ]]; then
  source .venv/bin/activate
fi

if [[ -f ".env" ]]; then
  set -a
  source .env
  set +a
fi

if [[ -z "${OPENAI_API_KEY:-}" || "${OPENAI_API_KEY}" == "sk-REPLACE_ME" ]]; then
  echo "OPENAI_API_KEY is missing or still using placeholder value."
  echo "Set it in environment or .env file."
  exit 2
fi

PDF_PATH="${1:-GradeDistributionsDB/Fall2023/grd20233EN.pdf}"
OUTPUT_DIR="${2:-eval_output/en_fall2023}"
MODEL="${OPENAI_MODEL:-gpt-4.1-mini}"

python3 scripts/evaluate_openai_vs_legacy.py \
  --pdf "$PDF_PATH" \
  --output-dir "$OUTPUT_DIR" \
  --model "$MODEL"
