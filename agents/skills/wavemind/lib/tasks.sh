#!/usr/bin/env bash
# WaveMind task management — daily tasks + recurring habits
# Data lives in agents/skills/wavemind/data/tasks/ (gitignored)
# Requires: jq

set -euo pipefail

if ! command -v jq &>/dev/null; then
  echo "Error: jq is required but not installed."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$(cd "$SCRIPT_DIR/../data" && pwd)"
TASKS_DIR="$DATA_DIR/tasks"
HABITS_FILE="$DATA_DIR/habits.json"

mkdir -p "$TASKS_DIR"

# Get today's date in YYYY-MM-DD format
today() {
  date +%Y-%m-%d
}

# Get today's task file
today_file() {
  echo "$TASKS_DIR/$(today).json"
}

# Initialize today's task file if it doesn't exist
init_today() {
  local file
  file="$(today_file)"
  if [ ! -f "$file" ]; then
    echo '{"date":"'"$(today)"'","tasks":[],"next_id":1}' | jq '.' > "$file"
  fi
}

# Initialize habits file if it doesn't exist
init_habits() {
  if [ ! -f "$HABITS_FILE" ]; then
    jq -n '[
      {"id": 1, "name": "Post 1 tweet", "frequency": "daily", "target": 1},
      {"id": 2, "name": "Interact with 3 tweets", "frequency": "daily", "target": 3}
    ]' > "$HABITS_FILE"
  fi
}

# Get today's habit tracking file
habits_today_file() {
  echo "$TASKS_DIR/habits-$(today).json"
}

init_habits_today() {
  local file
  file="$(habits_today_file)"
  if [ ! -f "$file" ]; then
    echo '{}' > "$file"
  fi
}

command="${1:?Usage: tasks.sh <today|add|done|undone|habit|habit-log|week>}"
shift

case "$command" in
  today)
    # Show today's tasks and habit status
    init_today
    init_habits
    init_habits_today
    echo "=== $(today) ==="
    echo ""
    echo "TASKS:"
    local_file="$(today_file)"
    task_count=$(jq '.tasks | length' "$local_file")
    if [ "$task_count" -eq 0 ]; then
      echo "  (no tasks yet)"
    else
      jq -r '.tasks[] | "  \(if .done then "✅" else "⬜" end) #\(.id) \(.text)"' "$local_file"
    fi
    echo ""
    echo "HABITS:"
    habits_file="$(habits_today_file)"
    jq -r --slurpfile tracking "$habits_file" '.[] |
      .id as $id |
      .name as $name |
      .target as $target |
      ($tracking[0][($id | tostring)] // 0) as $current |
      "  \(if $current >= $target then "✅" else "⬜" end) \($name) (\($current)/\($target))"
    ' "$HABITS_FILE"
    ;;

  add)
    # Add a task: tasks.sh add "Write ZAI proposal"
    text="${1:?Usage: tasks.sh add \"task description\"}"
    init_today
    local_file="$(today_file)"
    next_id=$(jq '.next_id' "$local_file")
    tmp="$local_file.tmp"
    jq --arg text "$text" --arg id "$next_id" '
      .tasks += [{"id": ($id | tonumber), "text": $text, "done": false}] |
      .next_id = (($id | tonumber) + 1)
    ' "$local_file" > "$tmp" && mv "$tmp" "$local_file"
    echo "Added task #$next_id: $text"
    ;;

  done)
    # Mark a task as done: tasks.sh done 3
    task_id="${1:?Usage: tasks.sh done <task-id>}"
    init_today
    local_file="$(today_file)"
    tmp="$local_file.tmp"
    jq --arg id "$task_id" '
      .tasks = [.tasks[] | if .id == ($id | tonumber) then .done = true else . end]
    ' "$local_file" > "$tmp" && mv "$tmp" "$local_file"
    echo "Marked task #$task_id as done."
    ;;

  undone)
    # Unmark a task: tasks.sh undone 3
    task_id="${1:?Usage: tasks.sh undone <task-id>}"
    init_today
    local_file="$(today_file)"
    tmp="$local_file.tmp"
    jq --arg id "$task_id" '
      .tasks = [.tasks[] | if .id == ($id | tonumber) then .done = false else . end]
    ' "$local_file" > "$tmp" && mv "$tmp" "$local_file"
    echo "Unmarked task #$task_id."
    ;;

  habit)
    # Show habit definitions and today's progress
    init_habits
    init_habits_today
    habits_file="$(habits_today_file)"
    jq -r --slurpfile tracking "$habits_file" '.[] |
      .id as $id |
      .name as $name |
      .target as $target |
      ($tracking[0][($id | tostring)] // 0) as $current |
      "\(if $current >= $target then "✅" else "⬜" end) \($name) — \($current)/\($target)"
    ' "$HABITS_FILE"
    ;;

  habit-log)
    # Log progress on a habit: tasks.sh habit-log 1 [count]
    habit_id="${1:?Usage: tasks.sh habit-log <habit-id> [count]}"
    count="${2:-1}"
    init_habits
    init_habits_today
    habits_file="$(habits_today_file)"
    tmp="$habits_file.tmp"
    jq --arg id "$habit_id" --arg count "$count" '
      .[$id] = ((.[$id] // 0) + ($count | tonumber))
    ' "$habits_file" > "$tmp" && mv "$tmp" "$habits_file"
    current=$(jq --arg id "$habit_id" '.[$id] // 0' "$habits_file")
    habit_name=$(jq -r --arg id "$habit_id" '.[] | select(.id == ($id | tonumber)) | .name' "$HABITS_FILE")
    echo "Logged $count for \"$habit_name\" (now $current total today)."
    ;;

  week)
    # Weekly review — show all tasks from the past 7 days
    echo "=== Weekly Review ==="
    for i in $(seq 0 6); do
      day=$(date -d "$(today) - $i days" +%Y-%m-%d 2>/dev/null || date -v-${i}d +%Y-%m-%d 2>/dev/null)
      file="$TASKS_DIR/$day.json"
      if [ -f "$file" ]; then
        total=$(jq '.tasks | length' "$file")
        completed=$(jq '[.tasks[] | select(.done)] | length' "$file")
        echo ""
        echo "$day: $completed/$total tasks done"
        jq -r '.tasks[] | "  \(if .done then "✅" else "⬜" end) \(.text)"' "$file"
      fi
    done
    ;;

  *)
    echo "Unknown command: $command"
    echo "Usage: tasks.sh <today|add|done|undone|habit|habit-log|week>"
    exit 1
    ;;
esac
