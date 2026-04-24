---
type: research-report
topic: Claude Max ToS — multi-agent usage on Agent Computer
date: 2026-03-24
status: complete
requested-by: lilyzhng + genius-ceo
author: genius-researcher
---

# Claude Max ToS for Multi-Agent Usage — Definitive Answer

## TL;DR

Running 4 agents on one Claude Max 20x account ($200/mo) is fine at current usage (18-20%). Scaling to 25 agents would likely violate "ordinary, individual usage" terms. Use API keys (pay-per-token) for large-scale agent fleets.

## The Key Terms

Source: https://code.claude.com/docs/en/legal-and-compliance

### What's explicitly allowed:
- Claude Code on any device (local or remote)
- OAuth authentication for Claude Code and Claude.ai
- Running Claude Code with the `--channels` flag (Discord plugin)

### What's explicitly prohibited:
- Using OAuth tokens in "any other product, tool, or service — including the Agent SDK"
- Third-party developers routing requests through Max plan credentials
- Building products that offer Claude.ai login on behalf of users

### The gray area:
> "Advertised usage limits for Pro and Max plans assume **ordinary, individual usage** of Claude Code and the Agent SDK."

## Our Current Setup: 4 Agents

| Agent | Location | How it runs | ToS status |
|-------|----------|-------------|-----------|
| Jackie | Agent Computer VM | Claude Code + Discord plugin | **Likely fine** — Claude Code on a remote machine |
| CEO | Lily's local machine | Claude Code + Discord plugin | **Fine** — standard local usage |
| Builder | Lily's local machine | Claude Code + Discord plugin | **Fine** — standard local usage |
| Researcher | Lily's local machine | Claude Code + Discord plugin | **Fine** — standard local usage |

**Usage:** 18-20% of weekly allocation (Lily checked March 24). Well within limits.

**2x evening multiplier:** During off-peak hours, token allocation doubles — giving more headroom for autonomous overnight work.

## Why 4 Agents is Fine

1. **All 4 are Claude Code** — the OAuth token is being used for its intended purpose (Claude Code), not piped through a third-party tool.
2. **Agent Computer's `claude-login` is an OAuth flow** — same as logging into Claude Code on any machine. Anthropic could restrict this but hasn't.
3. **Usage is 18-20%** — well within "ordinary" territory. Not stress-testing the system.
4. **Only 1-2 run concurrently most of the time** — Jackie is always-on, others are session-based.

## Why 25 Agents Would Be Risky

1. **"Ordinary, individual usage"** — 25 simultaneous Claude Code instances is not ordinary individual usage by any definition.
2. **Throttling** — Max 20x reportedly has throttling at ~50 sessions/month. 25 agents running continuously would blow past this.
3. **Cost arbitrage** — $200/mo for 25 agents vs. ~$2000+/mo on API pricing. Anthropic would notice.
4. **Enforcement risk** — "Anthropic reserves the right to take measures to enforce these restrictions and may do so without prior notice."

## Recommendation

| Scale | Approach | Risk |
|-------|---------|------|
| **1-4 agents** | Claude Max 20x ($200/mo) | Low — ordinary usage pattern |
| **5-10 agents** | Ask Anthropic first (Cat Wu contact) | Medium — gray area |
| **10+ agents** | API keys via Claude Console | None — explicit per-token pricing |

**For SofaGenius right now:** Stay on Max 20x with 4 agents. Monitor usage weekly. If we want to scale beyond 4, ask Cat Wu at Anthropic for guidance before doing it.

**If we ever need 25 agents:** Use API keys. The API has explicit per-token pricing with no "ordinary usage" ambiguity. Cost will be higher but it's the legitimate path.

## Sources

- https://code.claude.com/docs/en/legal-and-compliance — Official legal docs (VERIFIED)
- https://support.claude.com/en/articles/11049741-what-is-the-max-plan — Max plan details (VERIFIED)
- https://32blog.com/en/claude-code/claude-code-multiple-instances-context-guide — Multi-instance analysis (SECONDARY)
- Lily's usage check: 18-20% on March 24 (FIRST-HAND)
