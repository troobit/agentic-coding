#!/bin/bash
# Expose the runner on shell PATH without copying it away from its skills.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${1:-$HOME/.local/bin}"
SOURCE="$SCRIPT_DIR/local_next_task.py"
TARGET="$BIN_DIR/local-next-task"

if [ -L "$TARGET" ] && [ "$(readlink "$TARGET")" = "$SOURCE" ]; then
    echo "Already installed: $TARGET"
elif [ -e "$TARGET" ] || [ -L "$TARGET" ]; then
    echo "Cannot install: $TARGET exists and is not this repo's runner" >&2
    exit 1
else
    mkdir -p "$BIN_DIR"
    ln -s "$SOURCE" "$TARGET"
    echo "Installed: $TARGET -> $SOURCE"
fi

case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *) echo "Add $BIN_DIR to PATH to use local-next-task from your shell." ;;
esac
