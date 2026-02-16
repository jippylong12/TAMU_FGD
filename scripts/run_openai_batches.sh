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

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/run_openai_batches.sh --mode <submit|wait|collect|full|status> --semester <fall|spring|summer> --year <YYYY> [options]

Examples:
  bash scripts/run_openai_batches.sh --mode full --semester fall --year 2023
  bash scripts/run_openai_batches.sh --mode wait --semester fall --year 2023
  bash scripts/run_openai_batches.sh --mode status --semester fall --year 2023
  bash scripts/run_openai_batches.sh --mode full --semester fall --year 2023 --force-all

Required:
  --mode          submit | wait | collect | full | status
  --semester      fall | spring | summer
  --year          4-digit year

Optional:
  --force-all                 Rerun already-completed outputs (default: skip completed)
  --semester-dir <name>       Override folder name (default: Fall2023/Spring2024/etc)
  --term-key <key>            Override term key (default: YYYY + 1|2|3)
  --label <name>              Override output label (default: fall2023/spring2024/etc)
  --output-root <path>        Override output root (default: eval_output/<label>_all)
  --pdf-glob <glob>           Override PDF glob
  --submit-delay-seconds <n>  Sleep after each submit (default: 0)
  --help

Environment:
  OPENAI_MODEL
  MAX_PAGES
  BATCH_POLL_SECONDS
  BATCH_MAX_WAIT_SECONDS
USAGE
}

MODE=""
SEASON=""
YEAR=""
SEMESTER_DIR=""
TERM_KEY=""
SEMESTER_LABEL=""
OUTPUT_ROOT=""
PDF_GLOB=""
SUBMIT_DELAY_SECONDS="0"
FORCE_ALL=0

to_title_case() {
  local lower="$1"
  printf '%s%s' "$(printf '%s' "${lower:0:1}" | tr '[:lower:]' '[:upper:]')" "${lower:1}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      [[ $# -ge 2 ]] || { echo "Missing value for --mode" >&2; exit 2; }
      MODE="$2"
      shift 2
      ;;
    --semester)
      [[ $# -ge 2 ]] || { echo "Missing value for --semester" >&2; exit 2; }
      SEASON="$(printf '%s' "$2" | tr '[:upper:]' '[:lower:]')"
      shift 2
      ;;
    --year)
      [[ $# -ge 2 ]] || { echo "Missing value for --year" >&2; exit 2; }
      YEAR="$2"
      shift 2
      ;;
    --force-all)
      FORCE_ALL=1
      shift
      ;;
    --semester-dir)
      [[ $# -ge 2 ]] || { echo "Missing value for --semester-dir" >&2; exit 2; }
      SEMESTER_DIR="$2"
      shift 2
      ;;
    --term-key)
      [[ $# -ge 2 ]] || { echo "Missing value for --term-key" >&2; exit 2; }
      TERM_KEY="$2"
      shift 2
      ;;
    --label)
      [[ $# -ge 2 ]] || { echo "Missing value for --label" >&2; exit 2; }
      SEMESTER_LABEL="$2"
      shift 2
      ;;
    --output-root)
      [[ $# -ge 2 ]] || { echo "Missing value for --output-root" >&2; exit 2; }
      OUTPUT_ROOT="$2"
      shift 2
      ;;
    --pdf-glob)
      [[ $# -ge 2 ]] || { echo "Missing value for --pdf-glob" >&2; exit 2; }
      PDF_GLOB="$2"
      shift 2
      ;;
    --submit-delay-seconds)
      [[ $# -ge 2 ]] || { echo "Missing value for --submit-delay-seconds" >&2; exit 2; }
      SUBMIT_DELAY_SECONDS="$2"
      shift 2
      ;;
    --help|-h|help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

case "$MODE" in
  submit|wait|collect|full|status) ;;
  *)
    echo "Invalid --mode: ${MODE:-<missing>}" >&2
    usage
    exit 2
    ;;
esac

case "$SEASON" in
  spring|summer|fall) ;;
  *)
    echo "Invalid --semester: ${SEASON:-<missing>} (use spring|summer|fall)" >&2
    usage
    exit 2
    ;;
esac

if ! [[ "$YEAR" =~ ^[0-9]{4}$ ]]; then
  echo "Invalid --year: ${YEAR:-<missing>} (expected 4 digits)" >&2
  usage
  exit 2
fi

case "$SEASON" in
  spring) TERM_NUMBER="1" ;;
  summer) TERM_NUMBER="2" ;;
  fall) TERM_NUMBER="3" ;;
esac

if [[ -z "$SEMESTER_DIR" ]]; then
  SEMESTER_DIR="$(to_title_case "$SEASON")${YEAR}"
fi
if [[ -z "$TERM_KEY" ]]; then
  TERM_KEY="${YEAR}${TERM_NUMBER}"
fi
if [[ -z "$SEMESTER_LABEL" ]]; then
  SEMESTER_LABEL="${SEASON}${YEAR}"
fi
if [[ -z "$OUTPUT_ROOT" ]]; then
  OUTPUT_ROOT="eval_output/${SEMESTER_LABEL}_all"
fi
if [[ -z "$PDF_GLOB" ]]; then
  PDF_GLOB="GradeDistributionsDB/${SEMESTER_DIR}/grd${TERM_KEY}*.pdf"
fi

if [[ -f ".venv/bin/activate" ]]; then
  source .venv/bin/activate
fi
if [[ -f ".env" ]]; then
  set -a
  source .env
  set +a
fi
if [[ -z "${OPENAI_API_KEY:-}" || "${OPENAI_API_KEY}" == "sk-REPLACE_ME" ]]; then
  echo "OPENAI_API_KEY is missing or placeholder." >&2
  exit 2
fi

POLL_SECONDS="${BATCH_POLL_SECONDS:-30}"
MAX_WAIT_SECONDS="${BATCH_MAX_WAIT_SECONDS:-86400}"
MANIFEST_PATH="${OUTPUT_ROOT}/batch_manifest.json"

shopt -s nullglob
PDFS=( $PDF_GLOB )
shopt -u nullglob
if (( ${#PDFS[@]} == 0 )); then
  echo "No PDFs matched: $PDF_GLOB" >&2
  exit 2
fi
SORTED_PDFS=()
while IFS= read -r line; do
  SORTED_PDFS+=("$line")
done < <(printf '%s\n' "${PDFS[@]}" | sort)
PDFS=("${SORTED_PDFS[@]}")

derive_paths() {
  local pdf="$1"
  local basename code code_slug output_dir
  basename="$(basename "$pdf")"
  if [[ "$basename" != grd${TERM_KEY}*.pdf ]]; then
    echo ""
    return 0
  fi
  code="${basename#grd${TERM_KEY}}"
  code="${code%.pdf}"
  code_slug="$(printf '%s' "$code" | tr '[:upper:]' '[:lower:]')"
  output_dir="${OUTPUT_ROOT}/${code_slug}_${SEMESTER_LABEL}"
  echo "${code}|${output_dir}"
}

is_completed_output() {
  local output_dir="$1"
  [[ -s "${output_dir}/openai.json" ]]
}

has_batch_state() {
  local output_dir="$1"
  [[ -f "${output_dir}/batch_state/batch_state.json" ]]
}

run_eval() {
  local openai_mode="$1"
  local pdf="$2"
  local output_dir="$3"
  local verbose="${4:-0}"
  local args=(
    python3 scripts/evaluate_openai_vs_legacy.py
    --pdf "$pdf"
    --output-dir "$output_dir"
    --model "${OPENAI_MODEL:-gpt-4.1-mini}"
    --openai-mode "$openai_mode"
    --batch-state-dir "${output_dir}/batch_state"
    --batch-poll-seconds "$POLL_SECONDS"
    --batch-max-wait-seconds "$MAX_WAIT_SECONDS"
  )
  if [[ -n "${MAX_PAGES:-}" ]]; then
    args+=(--max-pages "$MAX_PAGES")
  fi
  if [[ "$verbose" == "1" ]]; then
    args+=(--verbose)
  fi
  PYTHONUNBUFFERED=1 "${args[@]}"
}

read_status_field() {
  local status_file="$1"
  python3 - "$status_file" <<'PY'
import json
import sys
from pathlib import Path
path = Path(sys.argv[1])
if not path.exists():
    print("")
    raise SystemExit(0)
with open(path, "r", encoding="utf-8") as handle:
    payload = json.load(handle)
print(payload.get("status", ""))
PY
}

update_manifest() {
  python3 scripts/update_openai_batch_manifest.py \
    --pdf-glob "$PDF_GLOB" \
    --output-root "$OUTPUT_ROOT" \
    --term-key "$TERM_KEY" \
    --label "$SEMESTER_LABEL" \
    --manifest-path "$MANIFEST_PATH" \
    --mode "$MODE" \
    --semester "$SEASON" \
    --year "$YEAR"
}

submit_phase() {
  local failures=0
  local pdf meta code output_dir
  for pdf in "${PDFS[@]}"; do
    meta="$(derive_paths "$pdf")"
    if [[ -z "$meta" ]]; then
      log "[WARN] submit skip unexpected filename: $(basename "$pdf")"
      continue
    fi
    code="${meta%%|*}"
    output_dir="${meta#*|}"
    if [[ "$FORCE_ALL" != "1" ]] && is_completed_output "$output_dir"; then
      log "[SKIP] submit code=${code} reason=already_completed output=${output_dir}"
      continue
    fi
    if [[ "$FORCE_ALL" != "1" ]] && has_batch_state "$output_dir"; then
      log "[SKIP] submit code=${code} reason=batch_state_exists output=${output_dir}"
      continue
    fi
    log "[submit] code=${code} pdf=${pdf} output=${output_dir}"
    if ! run_eval "batch-submit" "$pdf" "$output_dir" 1; then
      log "[ERROR] submit failed for ${pdf}"
      failures=$((failures + 1))
    fi
    if [[ "$SUBMIT_DELAY_SECONDS" != "0" ]]; then
      sleep "$SUBMIT_DELAY_SECONDS"
    fi
  done
  update_manifest
  return "$failures"
}

collect_phase() {
  local failures=0
  local pdf meta code output_dir
  for pdf in "${PDFS[@]}"; do
    meta="$(derive_paths "$pdf")"
    if [[ -z "$meta" ]]; then
      log "[WARN] collect skip unexpected filename: $(basename "$pdf")"
      continue
    fi
    code="${meta%%|*}"
    output_dir="${meta#*|}"
    if [[ "$FORCE_ALL" != "1" ]] && is_completed_output "$output_dir"; then
      log "[SKIP] collect code=${code} reason=already_completed output=${output_dir}"
      continue
    fi
    if ! has_batch_state "$output_dir"; then
      log "[ERROR] collect code=${code} reason=missing_batch_state output=${output_dir}"
      failures=$((failures + 1))
      continue
    fi
    log "[collect] code=${code} output=${output_dir}"
    if ! run_eval "batch-collect" "$pdf" "$output_dir" 1; then
      log "[ERROR] collect failed for ${pdf}"
      failures=$((failures + 1))
    fi
  done
  update_manifest
  return "$failures"
}

status_phase() {
  local done_count=0
  local in_progress_count=0
  local pending_count=0
  local ready_count=0
  local failed_count=0
  local status_errors=0
  local pdf meta code output_dir status
  for pdf in "${PDFS[@]}"; do
    meta="$(derive_paths "$pdf")"
    if [[ -z "$meta" ]]; then
      continue
    fi
    code="${meta%%|*}"
    output_dir="${meta#*|}"
    if is_completed_output "$output_dir"; then
      done_count=$((done_count + 1))
      log "[status] code=${code} state=done output=${output_dir}"
      continue
    fi
    if ! has_batch_state "$output_dir"; then
      pending_count=$((pending_count + 1))
      log "[status] code=${code} state=pending output=${output_dir}"
      continue
    fi
    if ! run_eval "batch-status" "$pdf" "$output_dir" 0; then
      status_errors=$((status_errors + 1))
      log "[status] code=${code} state=status_error output=${output_dir}"
      continue
    fi
    status="$(read_status_field "${output_dir}/batch_status.json")"
    case "$status" in
      completed)
        ready_count=$((ready_count + 1))
        log "[status] code=${code} state=ready_to_collect output=${output_dir}"
        ;;
      failed|expired|cancelled)
        failed_count=$((failed_count + 1))
        log "[status] code=${code} state=failed status=${status} output=${output_dir}"
        ;;
      *)
        in_progress_count=$((in_progress_count + 1))
        log "[status] code=${code} state=in_progress status=${status} output=${output_dir}"
        ;;
    esac
  done
  update_manifest
  local remaining=$((ready_count + in_progress_count + pending_count))
  log "[status-summary] done=${done_count} ready_to_collect=${ready_count} in_progress=${in_progress_count} pending=${pending_count} failed=${failed_count} status_errors=${status_errors} remaining=${remaining} manifest=${MANIFEST_PATH}"
  if (( failed_count > 0 || pending_count > 0 || status_errors > 0 )); then
    return 1
  fi
  return 0
}

wait_phase() {
  local start_ts now_ts elapsed
  local cycle=0
  start_ts="$(date +%s)"
  while true; do
    cycle=$((cycle + 1))
    local done_count=0
    local in_progress_count=0
    local pending_count=0
    local failed_count=0
    local collected_count=0
    local status_errors=0
    local pdf meta code output_dir status
    for pdf in "${PDFS[@]}"; do
      meta="$(derive_paths "$pdf")"
      if [[ -z "$meta" ]]; then
        continue
      fi
      code="${meta%%|*}"
      output_dir="${meta#*|}"
      if is_completed_output "$output_dir"; then
        done_count=$((done_count + 1))
        continue
      fi
      if ! has_batch_state "$output_dir"; then
        pending_count=$((pending_count + 1))
        continue
      fi
      if ! run_eval "batch-status" "$pdf" "$output_dir" 0; then
        status_errors=$((status_errors + 1))
        log "[wait] code=${code} state=status_error output=${output_dir}"
        continue
      fi
      status="$(read_status_field "${output_dir}/batch_status.json")"
      case "$status" in
        completed)
          log "[wait] code=${code} state=ready_to_collect output=${output_dir}"
          if run_eval "batch-collect" "$pdf" "$output_dir" 1; then
            collected_count=$((collected_count + 1))
            done_count=$((done_count + 1))
          else
            failed_count=$((failed_count + 1))
            log "[wait] code=${code} state=collect_failed output=${output_dir}"
          fi
          ;;
        failed|expired|cancelled)
          failed_count=$((failed_count + 1))
          log "[wait] code=${code} state=failed status=${status} output=${output_dir}"
          ;;
        *)
          in_progress_count=$((in_progress_count + 1))
          ;;
      esac
    done

    update_manifest
    local remaining=$((in_progress_count + pending_count))
    log "[wait-summary] cycle=${cycle} done=${done_count} collected=${collected_count} in_progress=${in_progress_count} pending=${pending_count} failed=${failed_count} status_errors=${status_errors} remaining=${remaining} manifest=${MANIFEST_PATH}"

    if (( remaining == 0 )); then
      if (( failed_count > 0 || status_errors > 0 || pending_count > 0 )); then
        return 1
      fi
      return 0
    fi
    if (( in_progress_count == 0 && pending_count > 0 )); then
      log "[wait-summary] no in-progress batches but pending items remain; exiting with failure."
      return 1
    fi

    now_ts="$(date +%s)"
    elapsed=$((now_ts - start_ts))
    if (( elapsed >= MAX_WAIT_SECONDS )); then
      log "[wait-summary] timeout reached (${MAX_WAIT_SECONDS}s)."
      return 1
    fi
    sleep "$POLL_SECONDS"
  done
}

log "Starting batch runner mode=${MODE} semester=${SEASON}${YEAR} term_key=${TERM_KEY} output_root=${OUTPUT_ROOT} pdf_count=${#PDFS[@]}"

failures=0
if [[ "$MODE" == "submit" ]]; then
  submit_phase || failures=$((failures + 1))
elif [[ "$MODE" == "collect" ]]; then
  collect_phase || failures=$((failures + 1))
elif [[ "$MODE" == "status" ]]; then
  status_phase || failures=$((failures + 1))
elif [[ "$MODE" == "wait" ]]; then
  wait_phase || failures=$((failures + 1))
elif [[ "$MODE" == "full" ]]; then
  submit_phase || failures=$((failures + 1))
  wait_phase || failures=$((failures + 1))
fi

if (( failures > 0 )); then
  log "[SUMMARY] mode=${MODE} failures=${failures} manifest=${MANIFEST_PATH}"
  exit 1
fi

log "[SUMMARY] mode=${MODE} success manifest=${MANIFEST_PATH}"
