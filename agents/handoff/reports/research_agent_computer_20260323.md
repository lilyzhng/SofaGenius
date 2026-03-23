---
type: research-report
topic: Persistent Agent Sandboxes — landscape, strategic implications, and action plan
date: 2026-03-23
status: complete
requested-by: lilyzhng (via Discord)
origin: https://x.com/i/status/2036123714157420959
developer-thread: https://x.com/i/status/2036157472256434236
---

# Persistent Agent Sandboxes — Research Report

## Origin

Lily found Agent Computer (agentcomputer.ai) via Twitter and asked the developer directly about their architecture. He confirmed the persistent disk sandbox was "completely developed in-house." This triggered a research deep-dive into the product, the competitive landscape, and what it means for SofaGenius.

- Original tweet: https://x.com/i/status/2036123714157420959
- Developer thread: https://x.com/i/status/2036157472256434236

## TL;DR

Persistent sandboxes for AI agents are becoming commodity infrastructure in 2026. Multiple well-funded players (Fly.io Sprites, Daytona, Agent Computer) are converging on the same solution: VMs with persistent state that survive restarts. **The infrastructure layer will be solved — our opportunity is the coordination and trust layer above it.**

---

## Part 1: Product Landscape

> **Note on data quality:** All performance numbers below are from vendor marketing pages or blog posts unless marked as [verified]. None have been independently benchmarked by us yet — that's part of the action plan.

### Agent Computer (agentcomputer.ai)
- **What:** Cloud computers (Ubuntu VMs) for AI agents
- **Spin-up time:** ~0.5s (vendor-claimed, unverified)
- **Persistent storage:** 25GB per VM, survives restarts (vendor-claimed)
- **Access:** SSH-based delegation from agents
- **Supported frameworks:** Claude, Codex, CUA
- **Pricing:** $20/mo for 25 VMs (2 vCPU, 8GB RAM each) — from pricing page
- **Enterprise:** Custom pricing via team@companion.ai
- **CLI:** `npm i -g aicomputer` → `computer create` / `computer ssh`
- **Related product:** Companion.ai (managed OpenClaw hosting with persistent sandbox)
- **"In-house" claim:** Developer confirmed building it in-house ([tweet thread](https://x.com/i/status/2036157472256434236)). **We don't know the underlying tech** — could be Firecracker, QEMU, or something custom. The architecture is unconfirmed.

### Fly.io Sprites (launched Jan 2026)
- **What:** Stateful sandboxes — persistent Linux VMs for AI agents
- **Spin-up:** 1-2s create, 300ms checkpoint/restore (vendor-claimed; [Simon Willison's analysis](https://simonwillison.net/2026/Jan/9/sprites-dev/) corroborates)
- **Storage:** 100GB — JuiceFS-like model (S3 backend, NVMe read-through cache, SQLite metadata via Litestream) — from Fly.io technical docs
- **Key feature:** Last 5 checkpoints mounted at `/.sprite/checkpoints` for rollback
- **Agent integration:** Pre-installed Claude Code skills that teach the agent how to use the sandbox environment
- **Most relevant to us** — we already use Fly.io for Jackie

### Daytona (Series A, Feb 2026 — $24M)
- **What:** Secure infra for AI-generated code execution
- **Spin-up:** Sub-90ms, some configs reach 27ms (vendor-claimed)
- **Approach:** OCI containers, rebuilding entire stack from first principles for AI agents
- **Persistence:** Snapshots + persistent filesystem
- **Open source:** github.com/daytonaio/daytona
- **SDKs:** Python, TypeScript, Go

### Others
| Product | Persistence | Speed | Notes |
|---------|-------------|-------|-------|
| **E2B** | Ephemeral | Fast | Firecracker, established but stateless |
| **K8s Agent Sandbox** | Via PVCs | Slower | CNCF SIG Apps, March 2026 — early stage, not production-ready |

---

## Part 2: Strategic Analysis — What This Means for SofaGenius

### First-order effect (happening now)
Persistent state for AI agents is being solved by multiple well-funded teams. Within 6-12 months, it will be reliable, cheap, and commoditized — like cloud compute before it.

### Second-order effects (where we should position)

**1. "Agents that work while you sleep" becomes default**
Right now only Jackie runs 24/7. When persistent sandboxes are cheap and reliable, all four agents (CEO, Builder, Researcher, Jackie) can run continuously. The bottleneck shifts from "agents aren't running" to "agents don't know how to work together." **Our coordination protocol (handoff files, PR workflow, Discord integration) is the defensible layer.**

**2. Agent coordination > agent compute**
Everyone will have persistent VMs. Not everyone will have a working multi-agent org with:
- Defined roles and scope ownership
- Async handoff protocol that works
- Agent-reviews-agent quality control
- Human-in-the-loop trust framework

**We're building this right now.** The PR review workflow, the handoff protocol, the scope split — these are the coordination patterns that become 10x more valuable when agents run 24/7.

**3. "How do I supervise autonomous agents?" becomes the key question**
Persistent agents working while you sleep need trust. Our PR review process (agent reviews agent, human approves) is an early answer. This is both a **product opportunity** (tooling for agent supervision) and a **content opportunity** (we have real experience to share).

### What to build toward

| Do Now | Do When Persistent State Matures |
|--------|----------------------------------|
| Keep coordination protocol portable (not coupled to Fly.io) | Move all agents to persistent sandboxes |
| Document multi-agent patterns (content) | Productize the coordination layer |
| Test one product (Agent Computer or Sprites) with a single agent | Scale to full team on persistent infra |
| Build agent evaluation/trust metrics (Owner: Researcher) | Sell/share the trust framework |

---

## Part 3: Action Plan

### Immediate (this week) — Owner: Researcher
- [ ] **Test Agent Computer** — sign up for $20/mo plan, spin up one VM, try running Researcher in it. Benchmark: actual spin-up time, persistent state reliability, DX quality. Report back with real numbers vs. vendor claims.
- [ ] **Compare with Sprites** — we're already on Fly.io. Try Sprites for one agent and benchmark the same dimensions. Compare UX/reliability side-by-side.
- [ ] **Keep coordination portable** — ensure our handoff protocol, CLAUDE.md configs, and skills work regardless of where the agent runs

### Short-term (this month)
- [ ] **Content piece** (Owner: CEO) — "What happens when AI agents never sleep? Lessons from running a 4-agent team"
- [ ] **Evaluate Daytona** (Owner: Researcher) — open source, claimed fastest cold starts, Python SDK. Benchmark for research workloads.
- [ ] **Publish benchmark results** (Owner: Researcher) — real numbers from testing, not vendor marketing. Share in handoff report.

### Medium-term (when we're ready to scale)
- [ ] Move agents off local launch to persistent sandboxes (Owner: Builder for infra, Researcher for testing)
- [ ] Implement shared filesystem for real-time multi-agent collaboration (Owner: Builder)
- [ ] Build agent activity dashboard — what did your agents do while you slept? (Owner: TBD)

---

## Sources

### Primary (vendor pages, direct communication)
- https://www.agentcomputer.ai/ — Agent Computer product/pricing page
- https://companion.ai/ — Companion.ai product page
- https://sprites.dev/ — Fly.io Sprites product page
- https://www.daytona.io/ — Daytona product page
- https://github.com/daytonaio/daytona — Daytona open source repo
- https://x.com/i/status/2036123714157420959 — Original tweet (Lily's find)
- https://x.com/i/status/2036157472256434236 — Developer confirmation thread (direct communication)

### Secondary (independent analysis, comparisons)
- https://simonwillison.net/2026/Jan/9/sprites-dev/ — Simon Willison's independent Sprites analysis
- https://northflank.com/blog/best-code-execution-sandbox-for-ai-agents — Sandbox comparison (third-party)
- https://northflank.com/blog/how-to-sandbox-ai-agents — Sandboxing strategies (third-party)

### Reference (technical background)
- https://firecracker-microvm.github.io/ — Firecracker microVM documentation
- https://kubernetes.io/blog/2026/03/20/running-agents-on-kubernetes-with-agent-sandbox/ — K8s Agent Sandbox announcement
