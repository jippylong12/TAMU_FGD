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

log "Starting OpenAI extraction run."

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
OPENAI_MODE="${OPENAI_MODE:-live}"
MAX_PAGES="${MAX_PAGES:-}"
MAX_WAIT_SECONDS="${BATCH_MAX_WAIT_SECONDS:-86400}"
POLL_SECONDS="${BATCH_POLL_SECONDS:-30}"
BATCH_ID="${BATCH_ID:-}"
BATCH_STATE_DIR="${BATCH_STATE_DIR:-$OUTPUT_DIR/batch_state}"
EXTRA_ARGS=(--verbose)
if [[ -n "$MAX_PAGES" ]]; then
  EXTRA_ARGS+=(--max-pages "$MAX_PAGES")
fi
EXTRA_ARGS+=(--openai-mode "$OPENAI_MODE")
EXTRA_ARGS+=(--batch-state-dir "$BATCH_STATE_DIR")
EXTRA_ARGS+=(--batch-poll-seconds "$POLL_SECONDS")
EXTRA_ARGS+=(--batch-max-wait-seconds "$MAX_WAIT_SECONDS")
if [[ -n "$BATCH_ID" ]]; then
  EXTRA_ARGS+=(--batch-id "$BATCH_ID")
fi

log "Input PDF: $PDF_PATH"
log "Output dir: $OUTPUT_DIR"
log "Model: $MODEL"
log "OpenAI mode: $OPENAI_MODE"
if [[ -n "$MAX_PAGES" ]]; then
  log "Max pages: $MAX_PAGES"
fi
if [[ "$OPENAI_MODE" != "live" ]]; then
  log "Batch state dir: $BATCH_STATE_DIR"
fi

PYTHONUNBUFFERED=1 python3 scripts/evaluate_openai_vs_legacy.py \
  --pdf "$PDF_PATH" \
  --output-dir "$OUTPUT_DIR" \
  --model "$MODEL" \
  "${EXTRA_ARGS[@]}"

log "OpenAI extraction run finished."
