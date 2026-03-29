#!/usr/bin/env bash
# WaveMind local JSON store — CRUD operations for artifacts
# Data lives in agents/skills/wavemind/data/ (gitignored)

set -euo pipefail

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
# Usage: add_artifact '{"id":"...","title":"...","source":"...","tags":[],"rounds":0,"word_count":0,"created_at":"...","file":"...","visualized":false}'
add_artifact() {
  local entry="$1"
  local tmp="$INDEX_FILE.tmp"

  # Read current index, append new entry
  if command -v jq &>/dev/null; then
    jq --argjson entry "$entry" '. += [$entry]' "$INDEX_FILE" > "$tmp" && mv "$tmp" "$INDEX_FILE"
  else
    # Fallback without jq: simple append
    local content
    content=$(cat "$INDEX_FILE")
    # Remove trailing ] and add new entry
    echo "${content%]}, ${entry}]" | sed 's/\[, /[/' > "$INDEX_FILE"
  fi
}

# Get an artifact entry by ID
# Usage: get_artifact "20260327-zai-prep"
get_artifact() {
  local id="$1"
  if command -v jq &>/dev/null; then
    jq --arg id "$id" '.[] | select(.id == $id)' "$INDEX_FILE"
  else
    grep -o "{[^}]*\"id\":\"$id\"[^}]*}" "$INDEX_FILE" || echo ""
  fi
}

# Mark an artifact as visualized
# Usage: mark_visualized "20260327-zai-prep"
mark_visualized() {
  local id="$1"
  local tmp="$INDEX_FILE.tmp"

  if command -v jq &>/dev/null; then
    jq --arg id "$id" 'map(if .id == $id then .visualized = true else . end)' "$INDEX_FILE" > "$tmp" && mv "$tmp" "$INDEX_FILE"
  fi
}

# List all artifacts
# Usage: list_artifacts
list_artifacts() {
  if command -v jq &>/dev/null; then
    jq -r '.[] | "\(.id)\t\(.title)\t\(.rounds) rounds\t\(.created_at)\t\(if .visualized then "visualized" else "not visualized" end)"' "$INDEX_FILE"
  else
    cat "$INDEX_FILE"
  fi
}

# Check if an artifact ID already exists
# Usage: artifact_exists "20260327-zai-prep"
artifact_exists() {
  local id="$1"
  if command -v jq &>/dev/null; then
    local count
    count=$(jq --arg id "$id" '[.[] | select(.id == $id)] | length' "$INDEX_FILE")
    [ "$count" -gt 0 ]
  else
    grep -q "\"id\":\"$id\"" "$INDEX_FILE"
  fi
}
