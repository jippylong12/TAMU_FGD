#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-full}"
shift || true

bash scripts/run_openai_batches.sh \
  --mode "$MODE" \
  --semester fall \
  --year 2023 \
  "$@"
