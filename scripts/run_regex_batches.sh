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
  scripts/run_regex_batches.sh --semester <fall|spring|summer> --year <YYYY> [--output-root <path>] [--force-all]

Examples:
  scripts/run_regex_batches.sh --semester fall --year 2023
  scripts/run_regex_batches.sh --semester spring --year 2024 --output-root eval_output/custom_regex_root
USAGE
}

semester=""
year=""
output_root=""
force_all=0

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
    --output-root)
      output_root="${2:-}"
      shift 2
      ;;
    --force-all)
      force_all=1
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

semester="$(echo "$semester" | tr '[:upper:]' '[:lower:]')"
case "$semester" in
  spring) term_digit="1" ;;
  summer) term_digit="2" ;;
  fall) term_digit="3" ;;
  *)
    echo "Invalid --semester: $semester (expected spring|summer|fall)" >&2
    exit 2
    ;;
esac

if [[ ! "$year" =~ ^[0-9]{4}$ ]]; then
  echo "Invalid --year: $year (expected 4-digit year)" >&2
  exit 2
fi

semester_title="$(echo "$semester" | awk '{print toupper(substr($0,1,1)) substr($0,2)}')"
semester_dir="${semester_title}${year}"
semester_label="${semester}${year}"
term_key="${year}${term_digit}"

if [[ -z "$output_root" ]]; then
  output_root="eval_output/${semester_label}_all_regex"
fi

input_dir="GradeDistributionsDB/${semester_dir}"
if [[ ! -d "$input_dir" ]]; then
  echo "Input directory not found: $input_dir" >&2
  exit 2
fi

log "Regex semester run starting."
log "Input dir: $input_dir"
log "Term key: $term_key"
log "Output root: $output_root"
log "Force all: $force_all"

total=0
completed=0
skipped=0
failed=0
found_any=0

for pdf in "$input_dir"/grd"${term_key}"*.pdf; do
  [[ -e "$pdf" ]] || continue
  found_any=1
  total=$((total + 1))

  base="$(basename "$pdf" .pdf)"
  code="${base#grd${term_key}}"
  code_lower="$(echo "$code" | tr '[:upper:]' '[:lower:]')"
  out_dir="${output_root}/${code_lower}_${semester_label}"
  out_json="${out_dir}/regex.json"

  if [[ "$force_all" != "1" && -s "$out_json" ]]; then
    log "[skip] code=$code output=$out_json already exists"
    skipped=$((skipped + 1))
    continue
  fi

  mkdir -p "$out_dir"
  log "[run] code=$code pdf=$pdf output=$out_json"
  if python3 scripts/extract_regex_json.py --pdf "$pdf" --output "$out_json"; then
    completed=$((completed + 1))
  else
    failed=$((failed + 1))
    log "[error] code=$code regex extraction failed"
  fi
done

if [[ "$found_any" != "1" ]]; then
  echo "No PDFs found matching: ${input_dir}/grd${term_key}*.pdf" >&2
  exit 2
fi

log "Regex semester run completed."
log "[summary] total=$total completed=$completed skipped=$skipped failed=$failed output_root=$output_root"

if [[ "$failed" -gt 0 ]]; then
  exit 1
fi

exit 0
