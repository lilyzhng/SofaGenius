# Sesame — MVP Spec

## First Principles Check

- **Who is the user?** AI agents (Claude Code, Open Claw, Cortex Code) and vibe coders who manage multiple projects
- **Where do they already live?** Inside agent harnesses that support skills
- **Does the distribution model match?** Yes — a skill is native to the agent platform. Portable across Claude Code forks.
- **What problem are we actually solving?** Not just one-time setup — ongoing key and project management across multiple projects. Humans forget which keys go where. Agents don't. The agent becomes the memory layer.
- **Why skill over CLI?** Skills are portable across Claude Code forks (Open Claw, Cortex Code). No npm publishing, no arg parsing. The agent calls `/sesame` directly.

## Problem

Setting up SaaS services is the #1 bottleneck for AI agents (and vibe-coders). Karpathy's MenuGen post nailed it: he spent most of his time "in the browser, moving between tabs and settings and configuring and gluing a monster."

But setup is only half the problem. The other half is **key management at scale.** As vibe coding grows, each person spins up more projects — each needing Stripe, Supabase, Vercel, etc. That's dozens of API keys across projects, and humans have short memory spans. Today people juggle `.env` files, dashboards, and sticky notes. It doesn't scale.

Previously, 1Password solved this for humans on the web. But agents live in the terminal. We need a **native solution for the agent era** — a persistent vault that the agent manages, so the human never has to remember which key goes where.

## What Sesame Does

A portable Claude Code skill with two layers:

### Layer 1: Vault (Key Management)
A persistent credential registry the agent owns. Single source of truth for all API keys across all projects.

```
~/.sesame/
├── vault.json          # Master registry — all keys, all projects
├── projects/
│   ├── menugen.json    # Which keys menugen uses
│   ├── saas-app.json   # Which keys saas-app uses
│   └── portfolio.json  # Which keys portfolio uses
```

**vault.json** stores every key, tagged with metadata:
```json
{
  "keys": {
    "stripe_test_acct_1": {
      "service": "stripe",
      "mode": "test",
      "key": "sk_test_abc123",
      "created": "2026-03-29",
      "used_by": ["menugen", "saas-app"]
    },
    "supabase_prod_menugen": {
      "service": "supabase",
      "mode": "prod",
      "url": "https://xxx.supabase.co",
      "anon_key": "eyJ...",
      "created": "2026-03-28",
      "used_by": ["menugen"]
    }
  }
}
```

### Layer 2: Provision + Inject (Service Setup)
Automates creating new service instances and injecting keys into projects.

```
/sesame new-project my-app
→ "You have existing keys for Stripe (test) and Supabase. Reuse these, or create new ones?"
→ Human: "Reuse Stripe, new Supabase"
→ Provisions new Supabase instance, reuses Stripe key
→ Writes .env for the project
→ Updates vault with new mappings

/sesame stripe
→ Provisions Stripe, stores in vault, injects into current project's .env

/sesame status
→ Shows all keys for current project + which are shared with other projects
```

### Why This Beats Raw .env Files

- `.env` is flat and per-project — no memory across projects
- Vault is the single source of truth. `.env` becomes a **generated artifact**, not manually maintained
- Agent can answer "which projects use this Stripe key?" instantly
- Key rotation = update vault, regenerate all affected `.env` files
- New project = pull from vault, not re-setup from scratch

## Skill Interface

```
/sesame <service> [options]     # Provision a service + store in vault
/sesame new-project <name>      # Start a new project, reuse or create keys
/sesame status                  # Show keys for current project
/sesame vault                   # Show all keys across all projects
/sesame inject                  # Generate .env from vault for current project
/sesame rotate <service>        # Rotate a key, update all affected projects
```

## Competitive Landscape

| Tool | What It Does | Gap |
|------|-------------|-----|
| **1Password / Bitwarden** | Human-facing password management (browser, GUI) | Not agent-native, no terminal/skill integration |
| **Infisical** | Open-source secrets manager, CLI + dashboard | Closest competitor — but focused on team secrets, not agent-driven project setup |
| **Composio** | Runtime API auth (OAuth token refresh, 250+ integrations) | Solves runtime calls, NOT initial project setup or key management |
| **Nango** | Product integration platform (OAuth flows, data syncs) | For building integrations, not bootstrapping projects |
| **dotenv-vault** | Encrypted .env syncing | Syncs existing .env files, doesn't provision or manage keys |
| **Individual CLIs** (stripe, vercel, supabase) | Per-service setup | Each works differently, no unified interface, no cross-project memory |

**Our gap:** Nobody provides an agent-native vault that provisions services, manages keys across projects, and generates `.env` files on demand. The "1Password for agents" doesn't exist yet.

## MVP Scope (Weekend Build)

### Phase 1: Vault + Provision (MVP)

**What we build:**
1. **Vault store** — `~/.sesame/vault.json` for key storage with project mappings
2. **3 service provisioners** — Stripe, Supabase, Vercel
3. **Inject command** — generate `.env` from vault for current project
4. **New project flow** — reuse or create keys with agent guidance

**What we defer:**
- Encryption at rest (use file permissions for now)
- Key rotation automation
- Team sharing / multi-user vaults
- GUI / dashboard

### Core: 3 Services

1. **Stripe** — payments (every SaaS needs this)
2. **Supabase** — database + auth (fastest Postgres setup)
3. **Vercel** — deployment (most common for Next.js)

### Auth Reality

**Honest labeling:** First-time setup for most services requires one human step (browser-based OAuth or pasting a token). Everything after that is fully automated.

| Service | First Time (human needed) | After That (fully automated) |
|---------|--------------------------|------------------------------|
| Stripe | `stripe login` opens browser | Keys read from vault |
| Supabase | Paste access token | Token stored in vault |
| Vercel | `vercel login` opens browser | Token stored in vault |

The value: the human does the one-time login. The agent handles provisioning, key extraction, vault storage, cross-project management, and `.env` generation — forever after.

### How Each Service Works

**Stripe:**
1. Check vault for existing Stripe keys
2. If reusing: pull from vault, skip to step 5
3. If new: check `~/.config/stripe/` for auth, run `stripe login` if needed
4. Create test-mode webhook endpoint, extract keys, store in vault
5. Inject into project `.env`

**Supabase:**
1. Check vault for existing Supabase credentials
2. If reusing: pull from vault, skip to step 5
3. If new: check for auth token, prompt if needed
4. Create project or link existing, extract URL + keys, store in vault
5. Inject into project `.env`

**Vercel:**
1. Check vault for existing Vercel token
2. If reusing: pull from vault, skip to step 5
3. If new: check for auth, run `vercel login` if needed
4. Link project, extract token + project ID, store in vault
5. Inject into project `.env`

### Security

- **Test-mode keys by default** — never provision production keys unless `--live` flag is explicitly passed
- **`.gitignore` enforcement** — auto-add `.env` to `.gitignore` on inject
- **File permissions** — vault.json created with `600` permissions (owner-only)
- **No vault in git** — `~/.sesame/` lives in home dir, never in project repo
- **Idempotency** — re-running a service command checks vault first, doesn't re-provision

### What We Ship

```
.claude/skills/sesame/
├── sesame.md              # Skill entry point (prompt + instructions)
├── services/
│   ├── stripe.sh          # Stripe provisioner
│   ├── supabase.sh        # Supabase provisioner
│   └── vercel.sh          # Vercel provisioner
└── lib/
    ├── vault.sh           # Vault read/write operations
    ├── inject.sh          # .env generation from vault
    └── output.sh          # Shared output helpers
```

### Portability

The skill is a directory that can be copied into any Claude Code-compatible agent:
- **Claude Code** — drop into `.claude/skills/`
- **Open Claw** — same skill format
- **Cortex Code** — same skill format
- **Any fork** — skills are just markdown + scripts

The vault (`~/.sesame/`) is per-machine, persists across projects.

## Distribution

- **GitHub repo** — share the skill directory, anyone can copy it in
- **Skills.sh** — submit to Vercel's skill registry for agent discovery
- **Direct copy** — agents install by copying the skill directory into their project

## Success Metrics (Weekend MVP)

- [ ] `~/.sesame/vault.json` stores and retrieves keys correctly
- [ ] `/sesame stripe` provisions and stores keys in vault
- [ ] `/sesame supabase` provisions and stores keys in vault
- [ ] `/sesame vercel` provisions and stores keys in vault
- [ ] `/sesame new-project` offers reuse of existing keys
- [ ] `/sesame inject` generates correct `.env` from vault
- [ ] An AI agent can set up a new project reusing existing keys without human help (after initial auth)
- [ ] Skill is portable — works in a fresh Claude Code project by copying the directory

## Post-MVP: The Full Vision

**Phase 2: Key Lifecycle**
- `/sesame rotate <service>` — rotate a key, update all affected `.env` files
- `/sesame audit` — show stale keys, unused keys, security warnings
- Encrypted vault (age/sops) for sensitive environments

**Phase 3: Team & Scale**
- Shared vaults for teams (like 1Password team vaults)
- `/sesame sync` — sync vault across machines
- More services: Auth0, Clerk, PlanetScale, Resend, Cloudflare
- `/sesame doctor` — verify all services healthy across all projects
- Community-contributed service provisioners

**Phase 4: Zero-Human**
- Auto-provision via API (no browser login needed) for services that support it
- Agent creates accounts, not just uses existing ones
- Full "idea to deployed app" with zero human intervention on infrastructure

## References

- [Karpathy's MenuGen post](https://karpathy.bearblog.dev/vibe-coding-menugen/) — the pain is real
- [Guillermo Rauch: "2026 is the year of Skills & CLIs"](https://x.com/rauchg/status/2029356560494018956)
- [Infisical](https://infisical.com) — closest existing product (open-source secrets manager)
- [Skills.sh](https://skills.sh) — distribution channel
- [Composio](https://composio.dev) — runtime auth, not setup
- [Google Workspace CLI](https://github.com/googleworkspace/cli) — gold standard for agent-first CLI design
