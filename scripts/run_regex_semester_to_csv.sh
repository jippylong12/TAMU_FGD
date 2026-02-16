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
  scripts/run_regex_semester_to_csv.sh --semester <spring|summer|fall> --year <YYYY> [--codes <CSV>] [--frontend-root <path>] [--download-insecure]

Examples:
  scripts/run_regex_semester_to_csv.sh --semester spring --year 2023
  scripts/run_regex_semester_to_csv.sh --semester summer --year 2023 --codes EN,BA,DT,DT_PROF
USAGE
}

semester=""
year=""
codes=""
frontend_root="../TAMU_FGD_FRONT_END"
download_insecure=0

# Legacy code list is kept for backward compatibility.
# scripts/download_pdfs_http.py applies rename fallback aliases
# (for example AC->AR, DT->DN, EH->ED, etc.) when needed.
DEFAULT_CODES="AC,AE,AG,AP,AT,BA,DT,DT_PROF,EH,EN,GB,GV,MN,MS,NS,PH,PM_PROF,QT,SL,SL_PROF,VF,VT,VT_PROF"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --semester)
      semester="${2:-}"
      shift 2
      ;;
    --year)
      year="${2:-}"
      shift 2
      ;;
    --codes)
      codes="${2:-}"
      shift 2
      ;;
    --frontend-root)
      frontend_root="${2:-}"
      shift 2
      ;;
    --download-insecure)
      download_insecure=1
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

if [[ -z "$semester" || -z "$year" ]]; then
  echo "Missing required arguments: --semester and --year" >&2
  usage
  exit 2
fi

if [[ -z "$codes" ]]; then
  codes="$DEFAULT_CODES"
fi

semester_lower="$(echo "$semester" | tr '[:upper:]' '[:lower:]')"
semester_upper="$(echo "$semester" | tr '[:lower:]' '[:upper:]')"
semester_label="${semester_lower}${year}"
eval_root="eval_output/${semester_label}_all_regex"
output_csv="GradeDistributionsDB/MasterDBs/MasterDB_${semester_label}_regex.csv"

log "Semester regex pipeline starting."
log "semester=$semester_lower year=$year"
log "codes=$codes"
log "eval_root=$eval_root"
log "output_csv=$output_csv"
log "download_insecure=$download_insecure"

log "Step 1/3: Download PDFs."
download_cmd=(python3 scripts/download_pdfs_http.py --year "$year" --semester "$semester_upper" --colleges "$codes")
if [[ "$download_insecure" == "1" ]]; then
  download_cmd+=(--insecure)
fi

if "${download_cmd[@]}"; then
  log "Download completed with all requested codes."
else
  log "Download reported some failures; continuing with available PDFs."
fi

log "Step 2/3: Run regex extraction batches."
bash scripts/run_regex_batches.sh --semester "$semester_lower" --year "$year"

log "Step 3/3: Generate semester MasterDB CSV from regex outputs."
bash scripts/generate_masterdb_from_eval_root.sh \
  "$eval_root" \
  "$output_csv" \
  "$frontend_root" \
  "regex.json"

log "Semester regex pipeline finished."
log "CSV: $output_csv"
