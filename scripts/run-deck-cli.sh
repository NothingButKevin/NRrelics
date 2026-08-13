#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
python="${NRRELICS_PYTHON:-$HOME/Mods/NRrelics-Deck/py312/bin/python}"

if [[ ! -x "$python" ]]; then
    printf 'Deck OCR Python was not found: %s\n' "$python" >&2
    exit 1
fi

exec "$python" "$project_dir/nrrelics.py" "$@"
