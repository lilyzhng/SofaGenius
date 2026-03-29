# What We Learned → What It Means for Data Agent v1

**Date:** 2026-03-28
**Author:** Genius Researcher
**For:** Lily, CEO, Builder

---

## The Big Picture (3 sentences)

The top AI labs (Anthropic, OpenAI, Alibaba) are all converging on one bet: **the winners in agentic AI will have better training environments, not better weights.** The agentic dataset landscape has exploded — we found 20+ datasets directly relevant to data agents, including 3 that are near-templates for what we're building. Combined with APEX benchmark analysis showing harness engineering outperforms model upgrades, the path is clear: **build the verification layer first — it's both the product AND the training environment.**

---

## 3 Key Findings → 3 Product Decisions

### Finding 1: Verification is the missing layer across ALL data agents
**Evidence:** Snowflake Cortex, Defog, Vanna, ThoughtSpot — none verify results. Only Databricks (via Quotient AI acquisition, March 2026) is moving toward this. Data trust is cited 2x more than any other blocker to AI adoption.

**Decision for v1:** Verification-first architecture. The eval layer is not a feature — it's the core product. Every query runs through a validator subagent that re-reads the question, checks SQL logic, runs sanity checks (row counts, value ranges, nulls). Ship with confidence scores visible to the user.

---

### Finding 2: Harness > Model (APEX proves it)
**Evidence:** On APEX-Agents (480 tasks, 63 MCP tools), Applied Compute jumped from #17 to #4 through harness changes alone. Claude Sonnet + strong scaffolding (52.7% SWE-bench) beat Claude Opus + weak scaffolding (52.0%). Vercel hit 100% by *removing* 80% of tools. Best models still only achieve ~36% Pass@1.

**Decision for v1:** Don't fine-tune a model. Invest in scaffolding — dynamic tool management, tiered context compaction, scratchpad memory, selective tool presentation. Use Claude via Agent SDK as the base model and win on harness engineering. This is also the fastest path to a strong APEX score for Lily's portfolio.

---

### Finding 3: Training environments are the new moat — and our product IS one
**Evidence:** Junyang Lin (ex-Qwen tech lead): "The agent IS the system. The model is just one of its parts." His team trained on 1.65M verifiable tasks in 20K parallel Docker environments. Critical finding: **trajectories trained on one scaffold don't transfer to others** — your training data must match your deployment scaffold.

**Decision for v1:** Design the agent to log full trajectories from day one. Every user session generates (query, trajectory, reward) tuples via the verification layer. This creates a self-improving flywheel:

```
Ship agent → Users query → Verification judges correctness
→ Trajectory + reward logged → RL training data generated automatically
→ Better agent → More users → More data → Repeat
```

We're not just building a product — we're building a training environment scoped to data analysis.

---

## Concrete v1 Architecture (from research)

| Component | What | Why (research-backed) |
|-----------|------|----------------------|
| **Orchestrator** | Main agent on Claude Agent SDK | Scaffold specificity — training data must match deployment scaffold |
| **Schema Inspector** | Subagent: understands database structure | DataMind-12K shows schema understanding is prerequisite |
| **Query Builder** | Subagent: NL → SQL | SQaLe (517K) + BIRD data proves execution-validated SQL training works |
| **Validator** | Subagent: verifies results against question | ExCoT-DPO shows execution feedback alone generates preference data — no humans needed |
| **Trajectory Logger** | Logs full agent traces | Qwen's MegaFlow: trajectory-level rewards require full traces |
| **Database: PostgreSQL** | v1 target | Broadest adoption, best MCP server support (`@modelcontextprotocol/server-postgres`) |

---

## Datasets We Should Use (prioritized)

| Priority | Dataset | Size | Why |
|----------|---------|------|-----|
| **Use now** | DataMind-12K | 12K trajectories | Closest to our product — data analysis agent trajectories, ICLR 2026 |
| **Use now** | Snowflake AWM-1K | 1K envs, 35K tools | SQL-backed MCP environments — almost a template for us |
| **Use now** | BIRD-Interact | 600 tasks | SQL agent trajectories with execution feedback, best models only 16% |
| **Foundation** | SQaLe | 517K | Massive execution-validated text-to-SQL |
| **Methodology** | ExCoT-DPO | — | How to generate preference data from execution feedback (no humans) |
| **RL infra** | Agent-R1 | — | Open-source RL training framework for when we have enough trajectories |

---

## What This Means for APEX (Lily's Portfolio)

APEX is the proof-of-concept for harness engineering. Our research shows:
1. **Harness improvements yield 3-5x more gain than model upgrades** on agentic benchmarks
2. **Tool selection matters more than tool count** — Vercel's "less is more" approach
3. **Context management is the #1 failure mode** — 65% of enterprise AI failures are context drift

If we nail the scaffolding for our data agent, the same techniques (tiered compaction, scratchpad memory, dynamic tool management) directly apply to APEX. One investment, two outcomes: product + benchmark score.

---

## One-Line Summary

**Build verification-first, log everything, win on scaffolding — the product becomes the training environment.**
