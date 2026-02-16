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
  scripts/run_regex_terms_to_masterdb.sh --term <spring:2023> [--term <summer:2023> ...] [--codes <CSV>] [--download-insecure]

Examples:
  scripts/run_regex_terms_to_masterdb.sh --term spring:2023 --term summer:2023 --download-insecure
  scripts/run_regex_terms_to_masterdb.sh --term fall:2023 --codes EN,BA,DT,DT_PROF
USAGE
}

terms=()
codes=""
download_insecure=0
frontend_root="../TAMU_FGD_FRONT_END"
output_csv="GradeDistributionsDB/MasterDBs/MasterDB.csv"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --term)
      terms+=("${2:-}")
      shift 2
      ;;
    --codes)
      codes="${2:-}"
      shift 2
      ;;
    --download-insecure)
      download_insecure=1
      shift
      ;;
    --frontend-root)
      frontend_root="${2:-}"
      shift 2
      ;;
    --output-csv)
      output_csv="${2:-}"
      shift 2
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

if (( ${#terms[@]} == 0 )); then
  echo "Provide at least one --term <semester:year>." >&2
  usage
  exit 2
fi

eval_roots=()

for term in "${terms[@]}"; do
  semester="${term%%:*}"
  year="${term##*:}"
  if [[ -z "$semester" || -z "$year" || "$semester" == "$term" || "$year" == "$term" ]]; then
    echo "Invalid --term value: $term (expected format semester:year, e.g. spring:2023)" >&2
    exit 2
  fi
  semester="$(echo "$semester" | tr '[:upper:]' '[:lower:]')"
  case "$semester" in
    spring|summer|fall) ;;
    *)
      echo "Invalid semester in term '$term': $semester (expected spring|summer|fall)" >&2
      exit 2
      ;;
  esac
  if [[ ! "$year" =~ ^[0-9]{4}$ ]]; then
    echo "Invalid year in term '$term': $year" >&2
    exit 2
  fi

  run_cmd=(
    bash scripts/run_regex_semester_to_csv.sh
    --semester "$semester"
    --year "$year"
    --frontend-root ""
  )
  if [[ -n "$codes" ]]; then
    run_cmd+=(--codes "$codes")
  fi
  if [[ "$download_insecure" == "1" ]]; then
    run_cmd+=(--download-insecure)
  fi

  log "Running semester pipeline for $semester:$year"
  "${run_cmd[@]}"
  eval_roots+=("eval_output/${semester}${year}_all_regex")
done

jsons=()
for root in "${eval_roots[@]}"; do
  while IFS= read -r path; do
    jsons+=("$path")
  done < <(find "$root" -type f -name "regex.json" | sort)
done

if (( ${#jsons[@]} == 0 )); then
  echo "No regex.json files found in selected term roots." >&2
  exit 2
fi

build_cmd=(
  python3 scripts/generate_masterdb_from_openai.py
  --output-csv "$output_csv"
  --verbose
)
if [[ -n "$frontend_root" ]]; then
  build_cmd+=(--frontend-root "$frontend_root")
fi
for path in "${jsons[@]}"; do
  build_cmd+=(--openai-json "$path")
done

log "Building combined MasterDB from ${#jsons[@]} regex.json file(s)."
"${build_cmd[@]}"

log "Done. Combined CSV: $output_csv"
