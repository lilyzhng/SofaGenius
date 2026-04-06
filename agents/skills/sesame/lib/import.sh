#!/usr/bin/env bash
# Sesame — import existing .env files into the vault

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/vault.sh"
source "${SCRIPT_DIR}/output.sh"

# Import a .env file into the vault.
# Usage: sesame_import <env_file> <project_name> [service_type]
# service_type defaults to "agent"
sesame_import() {
  local env_file="${1:?Usage: sesame_import <env_file> <project_name> [service_type]}"
  local project="${2:?Usage: sesame_import <env_file> <project_name> [service_type]}"
  local service="${3:-agent}"

  if [[ ! -f "$env_file" ]]; then
    sesame_error "File not found: ${env_file}"
    return 1
  fi

  vault_init

  local count=0
  while IFS= read -r line; do
    # Skip comments and blank lines
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

    # Parse KEY=VALUE
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      local env_var="${BASH_REMATCH[1]}"
      local key_val="${BASH_REMATCH[2]}"

      # Strip surrounding quotes if present
      key_val="${key_val#\"}"
      key_val="${key_val%\"}"
      key_val="${key_val#\'}"
      key_val="${key_val%\'}"

      local key_id="${project}_$(echo "$env_var" | tr '[:upper:]' '[:lower:]')"

      if vault_has_key "$key_id"; then
        sesame_info "Key ${key_id} already exists, skipping"
        continue
      fi

      vault_put_key "$key_id" "$(jq -n \
        --arg svc "$service" \
        --arg agent "$project" \
        --arg env_var "$env_var" \
        --arg key "$key_val" \
        --argjson used_by "[\"$project\"]" \
        '{service: $svc, agent: $agent, env_var: $env_var, key: $key, used_by: $used_by}'
      )"
      count=$((count + 1))
    fi
  done < "$env_file"

  if [[ $count -eq 0 ]]; then
    sesame_warn "No new keys imported from ${env_file}"
  else
    sesame_ok "Imported ${count} keys from ${env_file} into project '${project}'"
  fi
}

# Import all agent .env files from the agents directory.
# Usage: sesame_import_all <agents_dir>
sesame_import_all() {
  local agents_dir="${1:?Usage: sesame_import_all <agents_dir>}"

  if [[ ! -d "$agents_dir" ]]; then
    sesame_error "Directory not found: ${agents_dir}"
    return 1
  fi

  local found=0
  for agent_dir in "${agents_dir}"/genius-*/; do
    [[ ! -d "$agent_dir" ]] && continue
    local env_file="${agent_dir}.env"
    [[ ! -f "$env_file" ]] && continue

    local project
    project="$(basename "$agent_dir")"
    sesame_info "Importing ${project}..."
    sesame_import "$env_file" "$project"
    found=$((found + 1))
  done

  if [[ $found -eq 0 ]]; then
    sesame_warn "No .env files found in ${agents_dir}/genius-*/"
  else
    sesame_ok "Scanned ${found} agent(s)"
  fi
}
