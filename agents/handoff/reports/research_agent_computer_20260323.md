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

Persistent sandboxes for AI agents are becoming commodity infrastructure in 2026. Multiple well-funded players (Fly.io Sprites, Daytona, Agent Computer, Manus/Meta) are converging on the same solution: VMs with persistent state that survive restarts. **The infrastructure layer will be solved — our opportunity is the coordination and trust layer above it.**

---

## Part 1: Product Landscape

### Agent Computer (agentcomputer.ai)
- **What:** Cloud computers (Ubuntu VMs) for AI agents
- **Spin-up time:** ~0.5 seconds
- **Persistent storage:** 25GB per VM, survives restarts
- **Access:** SSH-based delegation from agents
- **Supported frameworks:** Claude, Codex, CUA
- **Pricing:** $20/mo for 25 VMs (2 vCPU, 8GB RAM each)
- **Enterprise:** Custom pricing via team@companion.ai
- **CLI:** `npm i -g aicomputer` → `computer create` / `computer ssh`
- **Related product:** Companion.ai (managed OpenClaw hosting with persistent sandbox)
- **"In-house" claim:** Developer confirmed; likely custom orchestration/persistence layer on top of Firecracker or similar, not a custom hypervisor

### Fly.io Sprites (launched Jan 2026)
- **What:** Stateful sandboxes — persistent Linux VMs for AI agents
- **Spin-up:** 1-2s create, **300ms checkpoint/restore**
- **Storage:** 100GB — JuiceFS-like model (S3 backend, NVMe read-through cache, SQLite metadata via Litestream)
- **Key feature:** Last 5 checkpoints mounted at `/.sprite/checkpoints` for rollback
- **Agent integration:** Pre-installed skills teach Claude how to use the sandbox
- **Most relevant to us** — we already use Fly.io for Jackie

### Daytona (Series A, Feb 2026 — $24M)
- **What:** Secure infra for AI-generated code execution
- **Spin-up:** Sub-90ms (some configs reach 27ms) — fastest in class
- **Approach:** OCI containers, rebuilding entire stack from first principles for AI agents
- **Persistence:** Snapshots + persistent filesystem
- **Open source:** github.com/daytonaio/daytona
- **SDKs:** Python, TypeScript, Go

### Others
| Product | Persistence | Speed | Notes |
|---------|-------------|-------|-------|
| **E2B** | Ephemeral | Fast | Firecracker, established but stateless |
| **Manus Sandbox** (Meta) | Unknown | Unknown | Acquired Dec 2025, launched Jan 2026 |
| **K8s Agent Sandbox** | Via PVCs | Slower | CNCF SIG Apps, March 2026 |

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

**We're building this right now.** The 18-PR session, the PR review workflow, the handoff files — these are the coordination patterns that become 10x more valuable when agents run 24/7.

**3. "How do I supervise autonomous agents?" becomes the key question**
Persistent agents working while you sleep need trust. Our PR review process (agent reviews agent, human approves) is an early answer. This is both a **product opportunity** (tooling for agent supervision) and a **content opportunity** (we have real experience to share).

### What to build toward

| Do Now | Do When Persistent State Matures |
|--------|----------------------------------|
| Keep coordination protocol portable (not coupled to Fly.io) | Move all agents to persistent sandboxes |
| Document multi-agent patterns (content) | Productize the coordination layer |
| Test one product (Agent Computer or Sprites) with a single agent | Scale to full team on persistent infra |
| Build agent evaluation/trust metrics | Sell/share the trust framework |

---

## Part 3: Action Plan

### Immediate (this week)
- [ ] **Test Agent Computer** — sign up for $20/mo plan, spin up one VM, try running Researcher in it. Evaluate: does persistent state actually work? How's the DX?
- [ ] **Compare with Sprites** — we're already on Fly.io. Try Sprites for one agent and compare UX/reliability.
- [ ] **Keep coordination portable** — ensure our handoff protocol, CLAUDE.md configs, and skills work regardless of where the agent runs

### Short-term (this month)
- [ ] **Content piece:** "What happens when AI agents never sleep? Lessons from running a 4-agent team" — this is the content angle from tonight's discussion
- [ ] **Evaluate Daytona** — open source, fastest cold starts, Python SDK. Could be good for research workloads.

### Medium-term (when we're ready to scale)
- [ ] Move agents off local launch to persistent sandboxes
- [ ] Implement shared filesystem for real-time multi-agent collaboration
- [ ] Build agent activity dashboard (what did your agents do while you slept?)

---

## Sources
- https://www.agentcomputer.ai/ — Agent Computer product page
- https://companion.ai/ — Companion.ai (related product, OpenClaw-based)
- https://sprites.dev/ — Fly.io Sprites
- https://www.daytona.io/ — Daytona
- https://github.com/daytonaio/daytona — Daytona open source repo
- https://simonwillison.net/2026/Jan/9/sprites-dev/ — Simon Willison's Sprites analysis
- https://northflank.com/blog/best-code-execution-sandbox-for-ai-agents — Sandbox comparison
- https://northflank.com/blog/how-to-sandbox-ai-agents — Sandboxing strategies
- https://firecracker-microvm.github.io/ — Firecracker microVM
- https://kubernetes.io/blog/2026/03/20/running-agents-on-kubernetes-with-agent-sandbox/ — K8s Agent Sandbox
- https://x.com/i/status/2036123714157420959 — Original tweet (Lily's find)
- https://x.com/i/status/2036157472256434236 — Developer confirmation thread
