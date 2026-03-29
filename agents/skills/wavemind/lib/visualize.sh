#!/usr/bin/env bash
# WaveMind visualize — helper for reading artifacts and managing output files
# The actual analysis + HTML generation is done by Claude via SKILL.md prompt.
# This script handles file I/O only.
#
# Usage:
#   bash visualize.sh read <artifact-id>    # Print artifact content for Claude to analyze
#   bash visualize.sh output <artifact-id>  # Print the output path for the HTML file
#   bash visualize.sh done <artifact-id>    # Mark artifact as visualized in index

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/store.sh"

command="${1:?Usage: visualize.sh <read|output|done> <artifact-id>}"
artifact_id="${2:?Usage: visualize.sh <read|output|done> <artifact-id>}"

case "$command" in
  read)
    # Validate artifact exists
    if ! artifact_exists "$artifact_id"; then
      echo "Error: Artifact '$artifact_id' not found in index."
      echo "Run /wavemind review to see available artifacts."
      exit 1
    fi

    # Print the artifact content for Claude to analyze
    artifact_file="$ARTIFACTS_DIR/$artifact_id.md"
    if [ ! -f "$artifact_file" ]; then
      echo "Error: Artifact file not found: $artifact_file"
      exit 1
    fi

    cat "$artifact_file"
    ;;

  output)
    # Print the output path where Claude should write the HTML
    echo "$VISUALS_DIR/$artifact_id.html"
    ;;

  done)
    # Mark artifact as visualized in index
    mark_visualized "$artifact_id"
    echo "Marked '$artifact_id' as visualized."
    ;;

  *)
    echo "Unknown command: $command"
    echo "Usage: visualize.sh <read|output|done> <artifact-id>"
    exit 1
    ;;
esac
