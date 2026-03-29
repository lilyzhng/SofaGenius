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
rounds=$(echo "$content" | grep -cE '^#{1,3} |^Round |^### Round' || echo "1")

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

# Parse tags into JSON array
if [ -n "$tags" ]; then
  tags_json=$(echo "$tags" | tr ',' '\n' | sed 's/^/"/;s/$/"/' | paste -sd',' | sed 's/^/[/;s/$/]/')
else
  tags_json="[]"
fi

# Create index entry
entry=$(cat <<ENTRY
{"id":"$id","title":"$title","source":"$source_type","tags":$tags_json,"rounds":$rounds,"word_count":$word_count,"created_at":"$(date -u +%Y-%m-%dT%H:%M:%SZ)","file":"artifacts/$id.md","visualized":false}
ENTRY
)

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
