#!/usr/bin/env bash
# Sesame — vault read/write operations
# Manages a local vault as the single source of truth for API keys

set -euo pipefail

# Vault lives in ~/.sesame/ by default. Override with SESAME_DIR env var.
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESAME_DIR="${SESAME_DIR:-${HOME}/.sesame}"
SESAME_VAULT="${SESAME_DIR}/vault.json"
SESAME_PROJECTS="${SESAME_DIR}/projects"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/output.sh"

# --- Init ---

vault_init() {
  if [[ ! -d "$SESAME_DIR" ]]; then
    mkdir -p "$SESAME_DIR" "$SESAME_PROJECTS"
    chmod 700 "$SESAME_DIR"
    sesame_info "Created vault at ${SESAME_DIR}"
  fi
  if [[ ! -f "$SESAME_VAULT" ]]; then
    echo '{"keys":{}}' > "$SESAME_VAULT"
    chmod 600 "$SESAME_VAULT"
    sesame_info "Initialized empty vault"
  fi
}

# --- Read ---

# Check if a key exists in the vault. Returns 0 if exists, 1 if not.
vault_has_key() {
  local key_id="$1"
  vault_init
  jq -e --arg id "$key_id" '.keys[$id] != null' "$SESAME_VAULT" >/dev/null 2>&1
}

# Get a specific field from a key entry. Prints the raw value.
vault_get_field() {
  local key_id="$1" field="$2"
  vault_init
  jq -r --arg id "$key_id" --arg f "$field" '.keys[$id][$f] // empty' "$SESAME_VAULT"
}

# Get the full key entry as JSON.
vault_get_key() {
  local key_id="$1"
  vault_init
  jq --arg id "$key_id" '.keys[$id]' "$SESAME_VAULT"
}

# List all keys for a given service. Prints key IDs, one per line.
vault_list_service() {
  local service="$1"
  vault_init
  jq -r --arg svc "$service" '[.keys | to_entries[] | select(.value.service == $svc) | .key] | .[]' "$SESAME_VAULT"
}

# List all keys used by a project. Prints key IDs, one per line.
vault_list_project() {
  local project="$1"
  vault_init
  jq -r --arg proj "$project" '[.keys | to_entries[] | select(.value.used_by | index($proj)) | .key] | .[]' "$SESAME_VAULT"
}

# Show full vault contents (for /sesame vault).
vault_show() {
  vault_init
  jq '.' "$SESAME_VAULT"
}

# --- Write ---

# Store a key in the vault. Accepts key_id and a JSON object of fields.
# Usage: vault_put_key "stripe_test_acct_1" '{"service":"stripe","mode":"test","key":"sk_test_abc"}'
vault_put_key() {
  local key_id="$1" data="$2"
  vault_init
  local now
  now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  local tmp="${SESAME_VAULT}.tmp"
  jq --arg id "$key_id" --argjson data "$data" --arg now "$now" \
    '.keys[$id] = ($data + {created: $now, used_by: ($data.used_by // [])})' \
    "$SESAME_VAULT" > "$tmp"
  mv "$tmp" "$SESAME_VAULT"
  chmod 600 "$SESAME_VAULT"
  sesame_ok "Stored key: ${key_id}"
}

# Add a project to a key's used_by list (idempotent).
vault_link_project() {
  local key_id="$1" project="$2"
  vault_init
  local tmp="${SESAME_VAULT}.tmp"
  jq --arg id "$key_id" --arg proj "$project" \
    'if .keys[$id].used_by | index($proj) then . else .keys[$id].used_by += [$proj] end' \
    "$SESAME_VAULT" > "$tmp"
  mv "$tmp" "$SESAME_VAULT"
  chmod 600 "$SESAME_VAULT"
}

# Remove a key from the vault.
vault_remove_key() {
  local key_id="$1"
  vault_init
  local tmp="${SESAME_VAULT}.tmp"
  jq --arg id "$key_id" 'del(.keys[$id])' "$SESAME_VAULT" > "$tmp"
  mv "$tmp" "$SESAME_VAULT"
  chmod 600 "$SESAME_VAULT"
  sesame_ok "Removed key: ${key_id}"
}

# --- Project registry ---

# Save project config (which keys it uses).
project_save() {
  local project="$1"
  vault_init
  mkdir -p "$SESAME_PROJECTS"
  local keys
  keys=$(vault_list_project "$project" | jq -R . | jq -s .)
  echo "{\"project\":\"${project}\",\"keys\":${keys}}" | jq '.' > "${SESAME_PROJECTS}/${project}.json"
  sesame_ok "Saved project config: ${project}"
}

# Get the current project name from the directory name.
project_current() {
  basename "$(pwd)"
}
