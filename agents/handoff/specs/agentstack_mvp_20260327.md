# Doorman — MVP Spec

## Problem

Setting up SaaS services is the #1 bottleneck for AI agents (and vibe-coders). Karpathy's MenuGen post nailed it: he spent most of his time "in the browser, moving between tabs and settings and configuring and gluing a monster." He gave up on database entirely — "too much bear."

Agents can write code. They can't click through Stripe dashboards, configure OAuth in Google Cloud Console, or navigate DNS settings. The setup layer is invisible to LLMs.

**Every SaaS is shipping its own CLI** (Stripe, Vercel, Supabase, Google Workspace). But each one works differently, and there's no unified `init` command that wires everything up and outputs config to stdout.

## What Doorman Does

A universal CLI that sets up SaaS services for AI agents. One command per service, everything to stdout.

```bash
# Agent runs this, gets back API keys + config
doorman init stripe
# → outputs: STRIPE_SECRET_KEY=sk_test_... STRIPE_PUBLISHABLE_KEY=pk_test_...

doorman init supabase
# → outputs: SUPABASE_URL=https://xxx.supabase.co SUPABASE_ANON_KEY=eyJ...

doorman init vercel --project my-app
# → outputs: VERCEL_TOKEN=... VERCEL_PROJECT_ID=...
```

The agent reads stdout, sets env vars, and keeps building. No browser. No clicking. No "too much bear."

## Competitive Landscape

| Tool | What It Does | Gap |
|------|-------------|-----|
| **Composio** | Runtime API auth (OAuth token refresh, 250+ integrations) | Solves runtime calls, NOT initial project setup |
| **Nango** | Product integration platform (OAuth flows, data syncs) | For building integrations, not bootstrapping projects |
| **CLI-Anything** (HKUDS) | Auto-generates CLIs for desktop apps | Academic, not SaaS-focused |
| **Skills.sh** (Vercel) | Distributes SKILL.md files for agents | Installs instructions, not infrastructure |
| **Individual CLIs** (stripe, vercel, supabase) | Per-service setup | Each works differently, no unified interface |

**Our gap:** Nobody solves "run one command to get Service X wired up and outputting config to stdout." The setup layer between "I want to use Stripe" and "I have STRIPE_SECRET_KEY in my env."

## MVP Scope (Weekend Build)

### Core: 3 Services

Pick the 3 most common services for a typical web app:

1. **Stripe** — payments (every SaaS needs this)
2. **Supabase** — database + auth (fastest Postgres setup)
3. **Vercel** — deployment (most common for Next.js)

### CLI Interface

```bash
doorman init <service> [options]
doorman list                    # show available services
doorman status                  # show configured services + env vars
```

**Output contract:** Every `init` command outputs `KEY=VALUE` pairs to stdout, one per line. Agents parse this trivially. Human-readable status goes to stderr.

```bash
# stdout (agent reads this)
STRIPE_SECRET_KEY=sk_test_abc123
STRIPE_PUBLISHABLE_KEY=pk_test_xyz789
STRIPE_WEBHOOK_SECRET=whsec_...

# stderr (human reads this)
✓ Stripe test mode configured
✓ Webhook endpoint registered at https://...
✓ 3 env vars exported
```

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
doorman/
├── bin/doorman          # CLI entry point
├── services/
│   ├── stripe.sh           # Stripe init script
│   ├── supabase.sh         # Supabase init script
│   └── vercel.sh           # Vercel init script
├── lib/
│   └── output.sh           # Shared stdout/stderr helpers
├── SKILL.md                # So agents know how to use it
└── package.json            # npm distribution
```

**Language:** Bash scripts. Agents already know bash. No build step. `npm install -g doorman-ai` and go.

### SKILL.md (for agent discovery)

```markdown
# Doorman

When you need to set up a SaaS service (payments, database, deployment, auth):

1. Run `doorman list` to see available services
2. Run `doorman init <service>` to configure it
3. Read stdout for KEY=VALUE pairs — add them to .env

Available services: stripe, supabase, vercel
```

## Distribution

- **npm:** `npm install -g doorman-ai` (main distribution)
- **Skills.sh:** Submit to Vercel's skill registry for agent discovery
- **SKILL.md:** Include in repo for Claude Code / Cortex Code auto-detection

## Success Metrics (Weekend MVP)

- [ ] `doorman init stripe` works end-to-end (outputs real test keys)
- [ ] `doorman init supabase` works end-to-end (outputs URL + keys)
- [ ] `doorman init vercel` works end-to-end (outputs token + project ID)
- [ ] An AI agent (Claude Code) can use Doorman to set up a project without human help
- [ ] Published to npm

## Post-MVP Ideas (Don't Build Yet)

- More services: Auth0, Clerk, PlanetScale, Resend, Cloudflare
- `doorman init all` — full stack in one command
- `doorman doctor` — verify all services healthy
- Plugin system — community-contributed service scripts
- MCP server wrapper — expose as MCP tool for agents that prefer MCP
- `.doorman.json` — project config file that remembers what's set up

## References

- [Karpathy's MenuGen post](https://karpathy.bearblog.dev/vibe-coding-menugen/) — the pain is real
- [Guillermo Rauch: "2026 is the year of Skills & CLIs"](https://x.com/rauchg/status/2029356560494018956)
- [CLI-Anything](https://github.com/HKUDS/CLI-Anything) — academic but directionally relevant
- [Skills.sh](https://skills.sh) — distribution channel
- [Composio](https://composio.dev) — runtime auth, not setup
- [Google Workspace CLI](https://github.com/googleworkspace/cli) — gold standard for agent-first CLI design
