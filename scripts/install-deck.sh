#!/usr/bin/env bash
# Install a transferred checkout without changing SteamOS's immutable system Python.
set -euo pipefail

SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR="${NRRELICS_INSTALL_DIR:-$HOME/Applications/NRrelics-Deck-CLI}"
BIN_DIR="$HOME/.local/bin"

if [[ -e "$INSTALL_DIR" && "$SOURCE_DIR" != "$INSTALL_DIR" ]]; then
    printf 'Refusing to overwrite existing installation: %s\n' "$INSTALL_DIR" >&2
    exit 1
fi

mkdir -p "$BIN_DIR"
if [[ "$SOURCE_DIR" != "$INSTALL_DIR" ]]; then
    mkdir -p "$(dirname -- "$INSTALL_DIR")"
    cp -a "$SOURCE_DIR" "$INSTALL_DIR"
fi

ln -sfn "$INSTALL_DIR/nrrelics.py" "$BIN_DIR/nrrelics"
printf 'Installed. Reconnect over SSH, then run: nrrelics status\n'
