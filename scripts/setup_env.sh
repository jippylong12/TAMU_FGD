#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Environment ready at $ROOT_DIR/.venv"
echo "Next:"
echo "  1) cp .env.example .env"
echo "  2) set OPENAI_API_KEY in .env"
echo "  3) run scripts/run_openai_comparison.sh"
