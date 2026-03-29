#!/usr/bin/env bash
# WaveMind capture — save a thinking artifact from a file path
# Usage: bash capture.sh <filepath> [title] [source] [tags]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/store.sh"

filepath="${1:?Usage: capture.sh <filepath> [title] [source] [tags]}"
title="${2:-}"
source_type="${3:-manual}"
tags="${4:-}"

# Validate file exists
if [ ! -f "$filepath" ]; then
  echo "Error: File not found: $filepath"
  exit 1
fi

# Read the file
content=$(cat "$filepath")
word_count=$(echo "$content" | wc -w | tr -d ' ')

# Count rounds/sections (look for ## headers or numbered rounds)
rounds=$(echo "$content" | grep -cE '^#{1,3} |^Round |^### Round' || true)
if [ "$rounds" -eq 0 ]; then
  rounds=1
fi

# Auto-generate title from filename if not provided
if [ -z "$title" ]; then
  title=$(basename "$filepath" .md | sed 's/_/ /g; s/-/ /g' | sed 's/\b\(.\)/\u\1/g')
fi

# Generate ID from today's date and title
today=$(date -u +%Y-%m-%d)
id=$(generate_id "$today" "$title")

# Check for duplicates
if artifact_exists "$id"; then
  echo "Artifact with ID '$id' already exists. Use a different title."
  exit 1
fi

# Copy file to artifacts directory
cp "$filepath" "$ARTIFACTS_DIR/$id.md"

# Parse tags into JSON array using jq for safe handling
if [ -n "$tags" ]; then
  tags_json=$(echo "$tags" | tr ',' '\n' | jq -R . | jq -s .)
else
  tags_json="[]"
fi

# Create index entry safely using jq
entry=$(jq -n \
  --arg id "$id" \
  --arg title "$title" \
  --arg source "$source_type" \
  --argjson tags "$tags_json" \
  --argjson rounds "$rounds" \
  --argjson wc "$word_count" \
  --arg created "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg file "artifacts/$id.md" \
  '{id:$id, title:$title, source:$source, tags:$tags, rounds:$rounds, word_count:$wc, created_at:$created, file:$file, visualized:false}')

# Add to index
add_artifact "$entry"

# Report
echo "Captured thinking artifact: \"$title\""
echo "  ID: $id"
echo "  Rounds: $rounds"
echo "  Words: $word_count"
echo "  Source: $source_type"
echo "  Stored: $ARTIFACTS_DIR/$id.md"
echo ""
echo "Run /wavemind visualize $id to generate a visual thought map."
