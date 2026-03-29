#!/usr/bin/env bash
# Sesame — Supabase provisioner
# Checks vault for existing credentials, provisions via Supabase CLI if needed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/vault.sh"
source "${SCRIPT_DIR}/../lib/output.sh"

# Provision Supabase for the current project.
# Usage: sesame_supabase [--force]
sesame_supabase() {
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

  sesame_info "Supabase — provisioning for project '${project}'"

  # Check vault for existing credentials
  local existing_keys
  existing_keys=$(vault_list_service "supabase")

  if [[ -n "$existing_keys" ]] && [[ "$force" != "true" ]]; then
    sesame_info "Found existing Supabase credentials in vault:"
    while IFS= read -r kid; do
      [[ -z "$kid" ]] && continue
      local url
      url=$(vault_get_field "$kid" "url")
      sesame_kv "$kid" "$url"
    done <<< "$existing_keys"

    # Offer reuse of first matching key
    local first_key
    first_key=$(echo "$existing_keys" | head -1)
    sesame_ok "Reusing existing credentials: ${first_key}"
    vault_link_project "$first_key" "$project"
    project_save "$project"
    _supabase_summary "$first_key"
    return 0
  fi

  # Check Supabase CLI is installed
  if ! command -v supabase &>/dev/null; then
    sesame_fatal "Supabase CLI not installed. Run: brew install supabase/tap/supabase"
  fi

  # Check auth — supabase CLI uses an access token
  local access_token=""
  if [[ -f "$HOME/.supabase/access-token" ]]; then
    access_token=$(cat "$HOME/.supabase/access-token")
  elif [[ -n "${SUPABASE_ACCESS_TOKEN:-}" ]]; then
    access_token="$SUPABASE_ACCESS_TOKEN"
  fi

  if [[ -z "$access_token" ]]; then
    sesame_warn "Supabase not authenticated."
    sesame_info "Please run: supabase login"
    sesame_info "Or paste your access token (from https://supabase.com/dashboard/account/tokens):"
    read -r access_token
    if [[ -n "$access_token" ]]; then
      mkdir -p "$HOME/.supabase"
      echo "$access_token" > "$HOME/.supabase/access-token"
      sesame_ok "Saved access token"
    else
      sesame_fatal "No access token provided"
    fi
  fi

  sesame_info "Supabase authenticated. Checking for existing projects..."

  # List projects and let user choose or create
  local projects_json
  projects_json=$(supabase projects list --output json 2>/dev/null || echo "[]")

  local project_count
  project_count=$(echo "$projects_json" | jq 'length')

  local supa_url="" supa_anon="" supa_service_role="" supa_project_ref=""

  if [[ "$project_count" -gt 0 ]]; then
    sesame_info "Found ${project_count} existing Supabase project(s):"
    echo "$projects_json" | jq -r '.[] | "  \(.name) — \(.id) (\(.region))"'
    sesame_info "Linking to first project. Override with --force to create new."

    supa_project_ref=$(echo "$projects_json" | jq -r '.[0].id')
    supa_url="https://${supa_project_ref}.supabase.co"

    # Get API keys
    local api_keys
    api_keys=$(supabase projects api-keys --project-ref "$supa_project_ref" --output json 2>/dev/null || echo "[]")
    supa_anon=$(echo "$api_keys" | jq -r '.[] | select(.name == "anon") | .api_key' 2>/dev/null || true)
    supa_service_role=$(echo "$api_keys" | jq -r '.[] | select(.name == "service_role") | .api_key' 2>/dev/null || true)
  else
    sesame_info "No existing projects found. Creating new project '${project}'..."
    # Create project — requires org ID
    local orgs
    orgs=$(supabase orgs list --output json 2>/dev/null || echo "[]")
    local org_id
    org_id=$(echo "$orgs" | jq -r '.[0].id // empty')

    if [[ -z "$org_id" ]]; then
      sesame_fatal "No Supabase organization found. Create one at https://supabase.com/dashboard"
    fi

    local db_pass
    db_pass=$(openssl rand -base64 24)

    local result
    result=$(supabase projects create "$project" \
      --org-id "$org_id" \
      --db-password "$db_pass" \
      --region us-east-1 \
      --output json 2>/dev/null || true)

    if [[ -z "$result" ]]; then
      sesame_fatal "Failed to create Supabase project"
    fi

    supa_project_ref=$(echo "$result" | jq -r '.id')
    supa_url="https://${supa_project_ref}.supabase.co"

    sesame_info "Project created. Waiting for API keys to be available..."
    sleep 5

    local api_keys
    api_keys=$(supabase projects api-keys --project-ref "$supa_project_ref" --output json 2>/dev/null || echo "[]")
    supa_anon=$(echo "$api_keys" | jq -r '.[] | select(.name == "anon") | .api_key' 2>/dev/null || true)
    supa_service_role=$(echo "$api_keys" | jq -r '.[] | select(.name == "service_role") | .api_key' 2>/dev/null || true)
  fi

  # Store in vault
  local key_id="supabase_${project}"
  local data
  data=$(jq -n \
    --arg svc "supabase" \
    --arg mode "prod" \
    --arg url "$supa_url" \
    --arg anon "$supa_anon" \
    --arg sr "$supa_service_role" \
    --arg ref "$supa_project_ref" \
    --arg proj "$project" \
    '{service: $svc, mode: $mode, url: $url, anon_key: $anon, service_role_key: $sr, project_ref: $ref, used_by: [$proj]}')

  vault_put_key "$key_id" "$data"
  project_save "$project"
  _supabase_summary "$key_id"
}

_supabase_summary() {
  local key_id="$1"
  sesame_ok "Supabase provisioned successfully!"
  sesame_kv "Key ID" "$key_id"
  sesame_kv "URL" "$(vault_get_field "$key_id" "url")"
  sesame_kv "Anon Key" "$(vault_get_field "$key_id" "anon_key" | head -c 20)..."
  local sr
  sr=$(vault_get_field "$key_id" "service_role_key")
  [[ -n "$sr" ]] && sesame_kv "Service Role Key" "${sr:0:20}..."
  sesame_info "Run /sesame inject to generate .env"
}
