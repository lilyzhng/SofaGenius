#!/usr/bin/env bash
# WaveMind render — shell wrapper for render.py
# Usage:
#   bash render.sh < analysis.json > output.html
#   bash render.sh analysis.json output.html
#   bash render.sh analysis.json  # prints to stdout

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/render.py" "$@"
