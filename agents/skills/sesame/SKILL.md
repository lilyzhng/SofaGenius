---
name: sesame
description: "Open Sesame! Agent-native key vault + service provisioning. Manages API keys across projects — the 1Password for agents."
argument-hint: <command> [service] [options]
allowed-tools: Bash, Read, Write, Edit
---

# Sesame — Agent Key Vault & Service Provisioner

You are running the Sesame skill. Sesame manages API keys in a persistent vault and provisions SaaS services for projects.

## Available Commands

The user invokes `/sesame <command>`. Parse the command and execute accordingly.

### `/sesame <service>` — Provision a service
Supported services: `stripe`, `supabase`, `vercel`

Run the corresponding provisioner script:
```bash
source agents/skills/sesame/services/<service>.sh
sesame_<service> [flags]
```

Flags:
- `--force` — skip vault reuse, provision fresh
- `--live` — (Stripe only) use live mode instead of test mode

### `/sesame status` — Show keys for current project
```bash
source agents/skills/sesame/lib/vault.sh
source agents/skills/sesame/lib/output.sh
project=$(project_current)
vault_list_project "$project" | while read -r kid; do
  vault_get_key "$kid"
done
```

### `/sesame vault` — Show all keys across all projects
```bash
source agents/skills/sesame/lib/vault.sh
vault_show
```

### `/sesame inject` — Generate .env from vault
```bash
source agents/skills/sesame/lib/inject.sh
sesame_inject
```

### `/sesame new-project <name>` — Start a new project with key reuse
1. Show all existing keys in vault grouped by service
2. For each service, ask: "Reuse existing key or create new?"
3. Provision new keys as needed
4. Link reused keys to the new project
5. Run inject to generate .env

## Behavior Rules

1. **Test mode by default** — never provision production/live keys unless `--live` is explicitly passed
2. **Vault first** — always check the vault before provisioning. Don't create duplicates.
3. **Idempotent** — running the same command twice should be safe (reuse existing keys)
4. **Human-in-the-loop for auth** — if a service CLI isn't authenticated, tell the user exactly what to run and stop. Don't loop or retry.
5. **Always run inject after provisioning** — remind the user or offer to generate .env
6. **.gitignore enforcement** — always ensure .env is in .gitignore after inject

## File Layout

```
agents/skills/sesame/
├── SKILL.md              # This file (skill entry point)
├── data/                 # Vault data (gitignored, runtime-only)
│   ├── .gitignore
│   ├── vault.json        # Master key registry
│   └── projects/         # Per-project key mappings
├── services/
│   ├── stripe.sh         # Stripe provisioner
│   ├── supabase.sh       # Supabase provisioner
│   └── vercel.sh         # Vercel provisioner
└── lib/
    ├── vault.sh          # Vault read/write operations
    ├── inject.sh         # .env generation from vault
    └── output.sh         # Shared output helpers
```

## Error Handling

- If a CLI tool is missing: tell the user the install command and stop
- If auth fails: tell the user the login command and stop
- If vault is corrupted: back up the file and reinitialize
- Never swallow errors silently — always report what happened
