# Sesame — MVP Spec

## First Principles Check

- **Who is the user?** AI agents (Claude Code, Open Claw, Cortex Code)
- **Where do they already live?** Inside agent harnesses that support skills
- **Does the distribution model match?** Yes — a skill is native to the agent platform. A CLI would require agents to shell out to a standalone tool they'd have to discover and install separately.
- **Why skill over CLI?** Skills are portable across Claude Code forks (Open Claw, Cortex Code). No npm publishing, no arg parsing overhead. The agent calls `/sesame stripe` directly — no shell needed.

## Problem

Setting up SaaS services is the #1 bottleneck for AI agents (and vibe-coders). Karpathy's MenuGen post nailed it: he spent most of his time "in the browser, moving between tabs and settings and configuring and gluing a monster." He gave up on database entirely — "too much bear."

Agents can write code. They can't click through Stripe dashboards, configure OAuth in Google Cloud Console, or navigate DNS settings. The setup layer is invisible to LLMs.

**Every SaaS is shipping its own CLI** (Stripe, Vercel, Supabase, Google Workspace). But each one works differently, and there's no unified setup flow that wires everything up and hands config back to the agent.

## What Sesame Does

A portable Claude Code skill that sets up SaaS services for AI agents. One command per service, config returned directly to the agent.

```
/sesame stripe
→ STRIPE_SECRET_KEY=sk_test_... STRIPE_PUBLISHABLE_KEY=pk_test_...

/sesame supabase
→ SUPABASE_URL=https://xxx.supabase.co SUPABASE_ANON_KEY=eyJ...

/sesame vercel --project my-app
→ VERCEL_TOKEN=... VERCEL_PROJECT_ID=...
```

The agent gets config directly, sets env vars, and keeps building. No browser. No clicking. No "too much bear."

## Competitive Landscape

| Tool | What It Does | Gap |
|------|-------------|-----|
| **Composio** | Runtime API auth (OAuth token refresh, 250+ integrations) | Solves runtime calls, NOT initial project setup |
| **Nango** | Product integration platform (OAuth flows, data syncs) | For building integrations, not bootstrapping projects |
| **CLI-Anything** (HKUDS) | Auto-generates CLIs for desktop apps | Academic, not SaaS-focused |
| **Skills.sh** (Vercel) | Distributes SKILL.md files for agents | Installs instructions, not infrastructure |
| **Individual CLIs** (stripe, vercel, supabase) | Per-service setup | Each works differently, no unified interface |

**Our gap:** Nobody solves "one command to get Service X wired up and config returned to the agent." The setup layer between "I want to use Stripe" and "I have STRIPE_SECRET_KEY in my env."

## MVP Scope (Weekend Build)

### Core: 3 Services

Pick the 3 most common services for a typical web app:

1. **Stripe** — payments (every SaaS needs this)
2. **Supabase** — database + auth (fastest Postgres setup)
3. **Vercel** — deployment (most common for Next.js)

### Skill Interface

```
/sesame <service> [options]
/sesame list                    # show available services
/sesame status                  # show configured services + env vars
```

**Output contract:** Every service command returns `KEY=VALUE` pairs that the agent can parse directly. Status messages are separate from the key output.

```
# Key output (agent parses this)
STRIPE_SECRET_KEY=sk_test_abc123
STRIPE_PUBLISHABLE_KEY=pk_test_xyz789
STRIPE_WEBHOOK_SECRET=whsec_...

# Status (informational)
✓ Stripe test mode configured
✓ Webhook endpoint registered at https://...
✓ 3 env vars exported
⚠️ Add .env to .gitignore to avoid committing secrets
```

### Auth Reality

**Honest labeling:** First-time setup for most services requires one human step (browser-based OAuth or pasting a token). Subsequent runs are fully automated.

| Service | First Time (human needed) | After That (fully automated) |
|---------|--------------------------|------------------------------|
| Stripe | `stripe login` opens browser | Keys read from `~/.config/stripe/` |
| Supabase | Paste access token or `--token` flag | Token cached in env |
| Vercel | `vercel login` opens browser | Token cached in `~/.vercel/` |

The value isn't eliminating the one-time login — it's **everything after**: key extraction, webhook setup, env var output, project linking. That's what agents can't do today.

### Security

- **Test-mode keys by default** — never output production keys unless `--live` flag is explicitly passed
- **`.gitignore` warning** — stderr warns on every init: "⚠️ Add .env to .gitignore"
- **No key storage** — Sesame reads from existing service configs, doesn't store keys itself
- **Idempotency** — running `sesame init stripe` twice outputs existing keys + stderr "already configured, use --force to reconfigure"

### How Each Service Works

**Stripe:**
1. Check for existing `~/.config/stripe/config.toml`
2. If not authenticated: `stripe login --interactive` (or accept `--api-key` flag)
3. Create test-mode webhook endpoint pointing to localhost
4. Output keys to stdout

**Supabase:**
1. Check for `SUPABASE_ACCESS_TOKEN` env var
2. If not set: prompt for token (or `--token` flag)
3. `supabase init` + `supabase start` for local dev, OR link to existing project
4. Output URL + keys to stdout

**Vercel:**
1. Check for existing Vercel auth
2. If not set: `vercel login` or accept `--token` flag
3. `vercel link --yes` to current project
4. Output token + project ID to stdout

### What We Ship

```
.claude/skills/sesame/
├── sesame.md              # Skill entry point (prompt + instructions)
├── services/
│   ├── stripe.sh          # Stripe setup script
│   ├── supabase.sh        # Supabase setup script
│   └── vercel.sh          # Vercel setup script
└── lib/
    └── output.sh          # Shared output helpers
```

**Language:** Bash scripts invoked by the skill. The skill prompt tells the agent how to call the scripts and parse the output. No npm package, no CLI arg parsing — just a skill file + bash scripts.

### Portability

The skill is a directory that can be copied into any Claude Code-compatible agent:
- **Claude Code** — drop into `.claude/skills/`
- **Open Claw** — same skill format
- **Cortex Code** — same skill format
- **Any fork** — skills are just markdown + scripts

## Distribution

- **GitHub repo** — share the skill directory, anyone can copy it in
- **Skills.sh** — submit to Vercel's skill registry for agent discovery
- **Direct copy** — agents install by copying the skill directory into their project

## Success Metrics (Weekend MVP)

- [ ] `/sesame stripe` works end-to-end (outputs real test keys)
- [ ] `/sesame supabase` works end-to-end (outputs URL + keys)
- [ ] `/sesame vercel` works end-to-end (outputs token + project ID)
- [ ] An AI agent (Claude Code) can use Sesame to set up a project without human help
- [ ] Skill is portable — works in a fresh Claude Code project by copying the directory

## Post-MVP Ideas (Don't Build Yet)

- More services: Auth0, Clerk, PlanetScale, Resend, Cloudflare
- `/sesame all` — full stack in one command
- `/sesame doctor` — verify all services healthy
- Community-contributed service scripts (PR to the skill repo)
- MCP server wrapper — expose as MCP tool for agents that prefer MCP
- `.sesame.json` — project config file that remembers what's set up

## References

- [Karpathy's MenuGen post](https://karpathy.bearblog.dev/vibe-coding-menugen/) — the pain is real
- [Guillermo Rauch: "2026 is the year of Skills & CLIs"](https://x.com/rauchg/status/2029356560494018956)
- [CLI-Anything](https://github.com/HKUDS/CLI-Anything) — academic but directionally relevant
- [Skills.sh](https://skills.sh) — distribution channel
- [Composio](https://composio.dev) — runtime auth, not setup
- [Google Workspace CLI](https://github.com/googleworkspace/cli) — gold standard for agent-first CLI design
