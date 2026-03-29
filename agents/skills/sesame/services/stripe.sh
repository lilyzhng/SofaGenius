#!/usr/bin/env bash
# Sesame — Stripe provisioner
# Checks vault for existing keys, provisions via Stripe CLI if needed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/vault.sh"
source "${SCRIPT_DIR}/../lib/output.sh"

# Provision Stripe for the current project.
# Usage: sesame_stripe [--live] [--force]
sesame_stripe() {
  local mode="test"
  local force=false
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --live) mode="live"; shift ;;
      --force) force=true; shift ;;
      *) shift ;;
    esac
  done

  local project
  project="$(project_current)"
  vault_init

  sesame_info "Stripe — provisioning for project '${project}' (mode: ${mode})"

  # Check vault for existing keys
  local existing_keys
  existing_keys=$(vault_list_service "stripe")

  if [[ -n "$existing_keys" ]] && [[ "$force" != "true" ]]; then
    sesame_info "Found existing Stripe keys in vault:"
    while IFS= read -r kid; do
      [[ -z "$kid" ]] && continue
      local km
      km=$(vault_get_field "$kid" "mode")
      sesame_kv "$kid" "mode=${km}"
    done <<< "$existing_keys"

    # Check if any match the requested mode
    local matching
    matching=$(echo "$existing_keys" | while IFS= read -r kid; do
      [[ -z "$kid" ]] && continue
      local km
      km=$(vault_get_field "$kid" "mode")
      [[ "$km" == "$mode" ]] && echo "$kid"
    done | head -1)

    if [[ -n "$matching" ]]; then
      sesame_ok "Reusing existing key: ${matching}"
      vault_link_project "$matching" "$project"
      project_save "$project"
      _stripe_summary "$matching"
      return 0
    fi
  fi

  # Check Stripe CLI is installed
  if ! command -v stripe &>/dev/null; then
    sesame_fatal "Stripe CLI not installed. Run: brew install stripe/stripe-cli/stripe"
  fi

  # Check Stripe CLI auth
  if ! stripe config --list &>/dev/null 2>&1; then
    sesame_warn "Stripe CLI not authenticated."
    sesame_info "Please run: stripe login"
    sesame_info "This opens a browser for one-time auth. After that, Sesame handles everything."
    return 1
  fi

  sesame_info "Stripe CLI authenticated. Extracting ${mode} keys..."

  # Extract keys
  local sk pk
  if [[ "$mode" == "test" ]]; then
    sk=$(stripe config --list 2>/dev/null | grep 'test_mode_api_key' | head -1 | awk '{print $NF}' || true)
    # If not in config, try the API
    if [[ -z "$sk" ]]; then
      sk=$(stripe api_keys list --mode test 2>/dev/null | grep 'sk_test_' | head -1 || true)
    fi
  else
    sk=$(stripe config --list 2>/dev/null | grep 'live_mode_api_key' | head -1 | awk '{print $NF}' || true)
  fi

  if [[ -z "$sk" ]]; then
    sesame_warn "Could not extract ${mode} secret key automatically."
    sesame_info "Please paste your Stripe ${mode} secret key (starts with sk_${mode}_):"
    read -r sk
  fi

  # Try to get publishable key
  pk=""
  if [[ "$mode" == "test" ]]; then
    pk=$(stripe config --list 2>/dev/null | grep 'test_mode_pub_key' | head -1 | awk '{print $NF}' || true)
  else
    pk=$(stripe config --list 2>/dev/null | grep 'live_mode_pub_key' | head -1 | awk '{print $NF}' || true)
  fi

  # Store in vault
  local key_id="stripe_${mode}_${project}"
  local data
  data=$(jq -n \
    --arg svc "stripe" \
    --arg mode "$mode" \
    --arg sk "$sk" \
    --arg pk "$pk" \
    --arg proj "$project" \
    '{service: $svc, mode: $mode, secret_key: $sk, publishable_key: $pk, used_by: [$proj]}')

  vault_put_key "$key_id" "$data"
  project_save "$project"
  _stripe_summary "$key_id"
}

_stripe_summary() {
  local key_id="$1"
  sesame_ok "Stripe provisioned successfully!"
  sesame_kv "Key ID" "$key_id"
  sesame_kv "Mode" "$(vault_get_field "$key_id" "mode")"
  sesame_kv "Secret Key" "$(vault_get_field "$key_id" "secret_key" | head -c 12)..."
  local pk
  pk=$(vault_get_field "$key_id" "publishable_key")
  [[ -n "$pk" ]] && sesame_kv "Publishable Key" "${pk:0:12}..."
  sesame_info "Run /sesame inject to generate .env"
}
