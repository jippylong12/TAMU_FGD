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
  scripts/run_regex_year_range_to_masterdb.sh \
    --start-year <YYYY> \
    --end-year <YYYY> \
    [--semesters <spring,summer,fall>] \
    [--jobs <N>] \
    [--output-root <path>] \
    [--output-csv <path>] \
    [--frontend-root <path>] \
    [--force-all] \
    [--strict]

Examples:
  scripts/run_regex_year_range_to_masterdb.sh --start-year 2012 --end-year 2023
  scripts/run_regex_year_range_to_masterdb.sh --start-year 2012 --end-year 2023 --semesters fall
USAGE
}

start_year=""
end_year=""
semesters_csv="spring,summer,fall"
jobs=4
output_root="eval_output/all_terms_regex"
output_csv="GradeDistributionsDB/MasterDBs/MasterDB.csv"
frontend_root="../TAMU_FGD_FRONT_END"
force_all=0
strict=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --start-year)
      start_year="${2:-}"
      shift 2
      ;;
    --end-year)
      end_year="${2:-}"
      shift 2
      ;;
    --semesters)
      semesters_csv="${2:-}"
      shift 2
      ;;
    --jobs)
      jobs="${2:-}"
      shift 2
      ;;
    --output-root)
      output_root="${2:-}"
      shift 2
      ;;
    --output-csv)
      output_csv="${2:-}"
      shift 2
      ;;
    --frontend-root)
      frontend_root="${2:-}"
      shift 2
      ;;
    --force-all)
      force_all=1
      shift
      ;;
    --strict)
      strict=1
      shift
      ;;
    -h|--help)
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

if [[ -z "$start_year" || -z "$end_year" ]]; then
  echo "Missing required arguments: --start-year and --end-year" >&2
  usage
  exit 2
fi

if [[ ! "$start_year" =~ ^[0-9]{4}$ || ! "$end_year" =~ ^[0-9]{4}$ ]]; then
  echo "Years must be 4-digit integers." >&2
  exit 2
fi

if [[ ! "$jobs" =~ ^[0-9]+$ || "$jobs" -lt 1 ]]; then
  echo "--jobs must be an integer >= 1" >&2
  exit 2
fi

if (( start_year > end_year )); then
  echo "--start-year must be <= --end-year" >&2
  exit 2
fi

raw_semesters=()
IFS=',' read -r -a raw_semesters <<< "$semesters_csv"
semesters=()
for raw in "${raw_semesters[@]}"; do
  token="$(echo "$raw" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
  case "$token" in
    spring|summer|fall)
      semesters+=("$token")
      ;;
    "")
      ;;
    *)
      echo "Invalid semester value: '$raw' (expected spring,summer,fall)" >&2
      exit 2
      ;;
  esac
done

if (( ${#semesters[@]} == 0 )); then
  echo "No valid semesters provided." >&2
  exit 2
fi

term_attempted=0
term_success=0
term_missing_dir=0
failed_terms=()
task_terms=()

log "Regex year-range run starting."
log "start_year=$start_year end_year=$end_year semesters=${semesters[*]}"
log "output_root=$output_root output_csv=$output_csv"
log "frontend_root=${frontend_root:-<disabled>} force_all=$force_all strict=$strict jobs=$jobs"

if [[ "$strict" == "1" && "$jobs" -gt 1 ]]; then
  log "Strict mode forces --jobs 1 for fail-fast behavior."
  jobs=1
fi

for ((year=start_year; year<=end_year; year++)); do
  for semester in "${semesters[@]}"; do
    semester_title="$(echo "$semester" | awk '{print toupper(substr($0,1,1)) substr($0,2)}')"
    term_dir="GradeDistributionsDB/${semester_title}${year}"
    if [[ ! -d "$term_dir" ]]; then
      log "[skip] missing term directory: $term_dir"
      term_missing_dir=$((term_missing_dir + 1))
      continue
    fi

    term_attempted=$((term_attempted + 1))
    task_terms+=("${semester}:${year}")
  done
done

if [[ "$term_attempted" -eq 0 ]]; then
  echo "No term directories were processed. Check GradeDistributionsDB folder names." >&2
  exit 2
fi

run_term() {
  local term="$1"
  local status_file="$2"
  local semester="${term%%:*}"
  local year="${term##*:}"
  local run_cmd=(
    bash scripts/run_regex_batches.sh
    --semester "$semester"
    --year "$year"
    --output-root "$output_root"
  )
  if [[ "$force_all" == "1" ]]; then
    run_cmd+=(--force-all)
  fi

  log "[term] parsing ${term}"
  if "${run_cmd[@]}"; then
    echo "ok|${term}" > "$status_file"
  else
    echo "fail|${term}" > "$status_file"
  fi
}

if [[ "$jobs" -eq 1 ]]; then
  for term in "${task_terms[@]}"; do
    status_file="/tmp/regex_year_range_${term//:/_}_$$.status"
    run_term "$term" "$status_file"
    result="$(cut -d'|' -f1 "$status_file" 2>/dev/null || echo fail)"
    rm -f "$status_file" 2>/dev/null || true
    if [[ "$result" == "ok" ]]; then
      term_success=$((term_success + 1))
    else
      failed_terms+=("$term")
      log "[term][fail] ${term}"
      if [[ "$strict" == "1" ]]; then
        exit 1
      fi
    fi
  done
else
  status_dir="$(mktemp -d "${TMPDIR:-/tmp}/regex-year-range.XXXXXX")"
  pids=()
  slot=0
  for term in "${task_terms[@]}"; do
    slot=$((slot + 1))
    run_term "$term" "$status_dir/$slot.status" &
    pids+=("$!")
    if [[ "${#pids[@]}" -ge "$jobs" ]]; then
      wait "${pids[0]}"
      pids=("${pids[@]:1}")
    fi
  done

  for pid in "${pids[@]}"; do
    wait "$pid"
  done

  for status_path in "$status_dir"/*.status; do
    [[ -e "$status_path" ]] || continue
    result="$(cut -d'|' -f1 "$status_path" 2>/dev/null || echo fail)"
    term="$(cut -d'|' -f2 "$status_path" 2>/dev/null || echo unknown)"
    if [[ "$result" == "ok" ]]; then
      term_success=$((term_success + 1))
    else
      failed_terms+=("$term")
      log "[term][fail] ${term}"
    fi
  done
  rm -rf "$status_dir"
fi

log "Building merged MasterDB from regex outputs."
bash scripts/generate_masterdb_from_eval_root.sh \
  "$output_root" \
  "$output_csv" \
  "$frontend_root" \
  "regex.json"

log "[summary] attempted=$term_attempted success=$term_success missing_dirs=$term_missing_dir failed_terms=${#failed_terms[@]}"
if (( ${#failed_terms[@]} > 0 )); then
  log "[summary] failed term list: ${failed_terms[*]}"
  exit 1
fi

log "Done. Combined MasterDB: $output_csv"
