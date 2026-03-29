#!/usr/bin/env bash
# Sesame — Vercel provisioner
# Checks vault for existing credentials, provisions via Vercel CLI if needed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/vault.sh"
source "${SCRIPT_DIR}/../lib/output.sh"

# Provision Vercel for the current project.
# Usage: sesame_vercel [--force]
sesame_vercel() {
  local force=false
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --force) force=true; shift ;;
      *) shift ;;
    esac
  done

  local project
  project="$(project_current)"
  vault_init

  sesame_info "Vercel — provisioning for project '${project}'"

  # Check vault for existing credentials
  local existing_keys
  existing_keys=$(vault_list_service "vercel")

  if [[ -n "$existing_keys" ]] && [[ "$force" != "true" ]]; then
    sesame_info "Found existing Vercel credentials in vault:"
    while IFS= read -r kid; do
      [[ -z "$kid" ]] && continue
      local pid
      pid=$(vault_get_field "$kid" "project_id")
      sesame_kv "$kid" "project_id=${pid}"
    done <<< "$existing_keys"

    local first_key
    first_key=$(echo "$existing_keys" | head -1)
    sesame_ok "Reusing existing credentials: ${first_key}"
    vault_link_project "$first_key" "$project"
    project_save "$project"
    _vercel_summary "$first_key"
    return 0
  fi

  # Check Vercel CLI is installed
  if ! command -v vercel &>/dev/null; then
    sesame_fatal "Vercel CLI not installed. Run: npm i -g vercel"
  fi

  # Check Vercel auth
  local whoami
  whoami=$(vercel whoami 2>/dev/null || true)

  if [[ -z "$whoami" ]]; then
    sesame_warn "Vercel CLI not authenticated."
    sesame_info "Please run: vercel login"
    sesame_info "This opens a browser for one-time auth. After that, Sesame handles everything."
    return 1
  fi

  sesame_info "Vercel authenticated as: ${whoami}"

  # Link project (or detect existing link)
  local vercel_dir=".vercel"
  local vercel_project_id="" vercel_org_id=""

  if [[ -f "${vercel_dir}/project.json" ]]; then
    vercel_project_id=$(jq -r '.projectId // empty' "${vercel_dir}/project.json")
    vercel_org_id=$(jq -r '.orgId // empty' "${vercel_dir}/project.json")
    sesame_info "Found existing Vercel link: ${vercel_project_id}"
  else
    sesame_info "Linking project to Vercel..."
    vercel link --yes 2>/dev/null || true

    if [[ -f "${vercel_dir}/project.json" ]]; then
      vercel_project_id=$(jq -r '.projectId // empty' "${vercel_dir}/project.json")
      vercel_org_id=$(jq -r '.orgId // empty' "${vercel_dir}/project.json")
    fi
  fi

  # Get token from Vercel config
  local vercel_token=""
  local vercel_auth_file="$HOME/.local/share/com.vercel.cli/auth.json"
  if [[ -f "$vercel_auth_file" ]]; then
    vercel_token=$(jq -r '.token // empty' "$vercel_auth_file")
  fi

  if [[ -z "$vercel_token" ]]; then
    sesame_warn "Could not extract Vercel token automatically."
    sesame_info "Please paste your Vercel token (from https://vercel.com/account/tokens):"
    read -r vercel_token
  fi

  # Store in vault
  local key_id="vercel_${project}"
  local data
  data=$(jq -n \
    --arg svc "vercel" \
    --arg mode "prod" \
    --arg token "$vercel_token" \
    --arg pid "${vercel_project_id}" \
    --arg oid "${vercel_org_id}" \
    --argjson used_by "[\"${project}\"]" \
    '{service: $svc, mode: $mode, token: $token, project_id: $pid, org_id: $oid, used_by: $used_by}')

  vault_put_key "$key_id" "$data"
  project_save "$project"
  _vercel_summary "$key_id"
}

_vercel_summary() {
  local key_id="$1"
  sesame_ok "Vercel provisioned successfully!"
  sesame_kv "Key ID" "$key_id"
  sesame_kv "Project ID" "$(vault_get_field "$key_id" "project_id")"
  sesame_kv "Org ID" "$(vault_get_field "$key_id" "org_id")"
  local token
  token=$(vault_get_field "$key_id" "token")
  [[ -n "$token" ]] && sesame_kv "Token" "${token:0:12}..."
  sesame_info "Run /sesame inject to generate .env"
}
