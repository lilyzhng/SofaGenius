#!/usr/bin/env bash
# Sesame — shared output helpers

set -euo pipefail

# Colors (disabled if not a terminal)
if [[ -t 1 ]]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[0;33m'
  BLUE='\033[0;34m'
  BOLD='\033[1m'
  NC='\033[0m'
else
  RED='' GREEN='' YELLOW='' BLUE='' BOLD='' NC=''
fi

sesame_info()  { echo -e "${BLUE}[sesame]${NC} $*"; }
sesame_ok()    { echo -e "${GREEN}[sesame]${NC} $*"; }
sesame_warn()  { echo -e "${YELLOW}[sesame]${NC} $*"; }
sesame_error() { echo -e "${RED}[sesame]${NC} $*" >&2; }
sesame_fatal() { sesame_error "$@"; exit 1; }

# Print a key=value pair for agent consumption
sesame_kv() {
  local key="$1" value="$2"
  echo -e "  ${BOLD}${key}${NC}: ${value}"
}
