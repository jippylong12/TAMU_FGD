#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

EVAL_ROOT="${1:-eval_output/fall2023_all}"
OUTPUT_CSV="${2:-GradeDistributionsDB/MasterDBs/MasterDB.csv}"
FRONTEND_ROOT="${3:-../TAMU_FGD_FRONT_END}"

if [[ ! -d "$EVAL_ROOT" ]]; then
  echo "Missing eval root directory: $EVAL_ROOT" >&2
  exit 2
fi

OPENAI_JSONS=()
while IFS= read -r line; do
  OPENAI_JSONS+=("$line")
done < <(find "$EVAL_ROOT" -type f -name "openai.json" | sort)
if (( ${#OPENAI_JSONS[@]} == 0 )); then
  echo "No openai.json files found under: $EVAL_ROOT" >&2
  exit 2
fi

cmd=(
  python3 scripts/generate_masterdb_from_openai.py
  --output-csv "$OUTPUT_CSV"
  --verbose
)

if [[ -n "$FRONTEND_ROOT" ]]; then
  cmd+=(--frontend-root "$FRONTEND_ROOT")
fi

for path in "${OPENAI_JSONS[@]}"; do
  cmd+=(--openai-json "$path")
done

echo "[INFO] Building MasterDB from ${#OPENAI_JSONS[@]} OpenAI output file(s)."
"${cmd[@]}"
