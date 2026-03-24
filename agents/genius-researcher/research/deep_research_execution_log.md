# Agent Computer Deep Research — Execution Log

## Session: 2026-03-24 ~00:45-08:00 PT

### Research Strategy
- Sub-agent 1: Community research (GitHub, Discord, Twitter, HN, Reddit)
- Sub-agent 2: API documentation research
- Main thread: Extract gotchas from Builder's PR #39, manual analysis

### Findings So Far

#### From Builder's PR #39 Setup Guide (VERIFIED — hands-on deployment)

**Critical finding: NO process auto-restart**
> "The Claude session dies if the web terminal tab closes. Need a process supervisor for true always-on (future improvement)."

This means:
- Jackie's Claude Code session runs in a web terminal
- If the terminal tab closes → session dies → Jackie goes offline
- There is NO supervisor/auto-restart mechanism yet
- This is the #1 reliability risk

**Other gotchas (all verified by Builder):**
1. No SCP support — SSH port 443 only, use pipe for file transfer
2. Plugin auto-update on restart overwrites custom fork
3. Self-mention doesn't trigger (bot ignores own messages)
4. SSH quoting is fragile for complex commands
5. Cron requires `apt install cron` — not pre-installed

**VM Specs (verified):**
- ~15GB RAM, ~30GB persistent disk
- Ubuntu, Python 3.12, Node 22, Git pre-installed
- Claude Code pre-installed
- SSH on port 443, VNC, web terminal
- Spin-up: ~0.3 seconds

**Cost:**
- $20/mo for 25 VMs
- Current usage: 1/25 (Jackie)

### Hypothesis Status

| # | Hypothesis | Status | Evidence | Source |
|---|-----------|--------|----------|--------|
| 1 | VMs stay up 24/7 | PARTIALLY TRUE | VM persists but Claude Code session dies if terminal closes | Builder PR #39 gotcha #4 |
| 2 | Context compression works in Discord mode | UNTESTED | Need 24-hour monitoring — cannot assume from CLI behavior | Unverified |
| 3 | Plugin persists across restarts | FALSE | Plugin overwrites on restart — must re-apply fork | Builder PR #39 gotcha #2 |
| 4 | Process auto-restarts after crash | FALSE | No supervisor mechanism — session dies with terminal | Builder PR #39 gotcha #4 |
| 5 | 25 VMs run simultaneously | UNTESTED | Only 1 VM used. No community data to validate. | No users found |
| 6 | Platform has community/support | FALSE | No GitHub repo, no Discord, no HN/Reddit presence, no user reviews | Sub-agent 1 search |
| 7 | API supports monitoring | TRUE | Metrics endpoint exists: GET /v1/computers/{id}/metrics | Sub-agent 2 API docs |
| 8 | API supports automation | TRUE | Full REST API with OpenAPI spec. No webhooks though. | Sub-agent 2 API docs |

### Sub-Agent 1 Results: Community Research (COMPLETED)

**Critical finding: Agent Computer has NO public community presence.**
- No public GitHub repo
- No Discord server or community forum found
- No real user reviews on Product Hunt, HN, Reddit, or dev forums
- No blog posts from users who deployed on Agent Computer
- Twitter/X has founder posts but no independent user experiences

**What this means:**
- We are likely among the earliest users of this platform
- No community to learn from (unlike Hermes which has GitHub issues, guides, forums)
- If something breaks, there's no community knowledge base — just vendor support
- The platform is very early-stage despite the polished UI

**Risk implication:** We're betting on an unproven platform with no community evidence. This is the opposite of what we did with Hermes (where Builder found 2 community guides and 5 production gotchas from GitHub issues). With Agent Computer, we ARE the community.

### Sub-Agent 2 Results: API Research (COMPLETED)

**API base URL:** `https://api.computer.agentcomputer.ai/v1`
**Auth:** Bearer token (`ac_live_` prefix)
**OpenAPI spec:** Available at `/openapi.json`

**What the API can do:**
- Machine CRUD: create, list, get, update, delete VMs
- Metrics: `GET /v1/computers/{id}/metrics` — CPU, memory, disk, network
- Agent sessions: create, manage, stream logs
- SSH key management
- Port forwarding
- File sharing between client and machine
- Firmware updates

**What the API CANNOT do (gaps):**
- No webhooks or event notifications — polling only
- No documented rate limits — implement exponential backoff
- No Python or JavaScript SDK — HTTP calls or CLI only
- No documented IP allowlisting

**Useful for us:**
- Metrics endpoint could be used for monitoring Jackie's resource usage
- Agent sessions API could automate deployments
- OpenAPI spec means we can generate a client if needed

### Issues Encountered
- Cannot SSH into Jackie's VM myself — need credentials/access from Builder
- Agent Computer has no public GitHub repo — can't read source code
- No community data to validate any claims — we're the first users
