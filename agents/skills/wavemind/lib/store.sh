#!/usr/bin/env bash
# WaveMind local JSON store — CRUD operations for artifacts
# Data lives in agents/skills/wavemind/data/ (gitignored)
# Requires: jq

set -euo pipefail

# Verify jq is available
if ! command -v jq &>/dev/null; then
  echo "Error: jq is required but not installed."
  exit 1
fi

# Resolve data directory relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$(cd "$SCRIPT_DIR/../data" && pwd)"
INDEX_FILE="$DATA_DIR/index.json"
ARTIFACTS_DIR="$DATA_DIR/artifacts"
VISUALS_DIR="$DATA_DIR/visuals"

# Ensure directories exist
mkdir -p "$ARTIFACTS_DIR" "$VISUALS_DIR"

# Initialize index if it doesn't exist
if [ ! -f "$INDEX_FILE" ]; then
  echo '[]' > "$INDEX_FILE"
fi

# Generate a slug-style ID from date and title
# Usage: generate_id "2026-03-27" "ZAI Ambassador Prep"
generate_id() {
  local date="$1"
  local title="$2"
  local date_part="${date//[-]}"
  # Convert title to lowercase, replace spaces with dashes, remove non-alphanumeric
  local title_part
  title_part=$(echo "$title" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g' | head -c 30)
  echo "${date_part}-${title_part}"
}

# Add an artifact to the index
# Usage: add_artifact '{"id":"...","title":"...",...}'
add_artifact() {
  local entry="$1"
  local tmp="$INDEX_FILE.tmp"
  jq --argjson entry "$entry" '. += [$entry]' "$INDEX_FILE" > "$tmp" && mv "$tmp" "$INDEX_FILE"
}

# Get an artifact entry by ID
# Usage: get_artifact "20260327-zai-prep"
get_artifact() {
  local id="$1"
  jq --arg id "$id" '.[] | select(.id == $id)' "$INDEX_FILE"
}

# Mark an artifact as visualized
# Usage: mark_visualized "20260327-zai-prep"
mark_visualized() {
  local id="$1"
  local tmp="$INDEX_FILE.tmp"
  jq --arg id "$id" 'map(if .id == $id then .visualized = true else . end)' "$INDEX_FILE" > "$tmp" && mv "$tmp" "$INDEX_FILE"
}

# List all artifacts
# Usage: list_artifacts
list_artifacts() {
  jq -r '.[] | "\(.id)\t\(.title)\t\(.rounds) rounds\t\(.created_at)\t\(if .visualized then "visualized" else "not visualized" end)"' "$INDEX_FILE"
}

# Check if an artifact ID already exists
# Usage: artifact_exists "20260327-zai-prep"
artifact_exists() {
  local id="$1"
  local count
  count=$(jq --arg id "$id" '[.[] | select(.id == $id)] | length' "$INDEX_FILE")
  [ "$count" -gt 0 ]
}
