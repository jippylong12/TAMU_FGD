#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

timestamp() {
  date +"%Y-%m-%d %H:%M:%S"
}

log() {
  echo "[$(timestamp)] $*"
}

log "Starting OpenAI comparison run."

if [[ -f ".venv/bin/activate" ]]; then
  log "Activating local virtual environment."
  source .venv/bin/activate
fi

if [[ -f ".env" ]]; then
  log "Loading environment variables from .env."
  set -a
  source .env
  set +a
fi

if [[ -z "${OPENAI_API_KEY:-}" || "${OPENAI_API_KEY}" == "sk-REPLACE_ME" ]]; then
  log "OPENAI_API_KEY is missing or still using placeholder value."
  log "Set it in environment or .env file."
  exit 2
fi

PDF_PATH="${1:-GradeDistributionsDB/Fall2023/grd20233EN.pdf}"
OUTPUT_DIR="${2:-eval_output/en_fall2023}"
MODEL="${OPENAI_MODEL:-gpt-4.1-mini}"
MAX_PAGES="${MAX_PAGES:-}"
EXTRA_ARGS=(--verbose)
if [[ -n "$MAX_PAGES" ]]; then
  EXTRA_ARGS+=(--max-pages "$MAX_PAGES")
fi

log "Input PDF: $PDF_PATH"
log "Output dir: $OUTPUT_DIR"
log "Model: $MODEL"
if [[ -n "$MAX_PAGES" ]]; then
  log "Max pages: $MAX_PAGES"
fi

PYTHONUNBUFFERED=1 python3 scripts/evaluate_openai_vs_legacy.py \
  --pdf "$PDF_PATH" \
  --output-dir "$OUTPUT_DIR" \
  --model "$MODEL" \
  "${EXTRA_ARGS[@]}"

log "OpenAI comparison run finished."
