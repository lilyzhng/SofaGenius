# Researcher Sessions — March 26-27, 2026

## Context
Multiple research sessions covering APEX strategy, dataset discovery, training environments, and Karpathy study.

---

## March 26: APEX Harness Strategy + Data Agent Direction

### Key Events
1. **Product direction decided:** Build a Data + Eval Agent — Lily chose this over alternatives
2. **APEX/Mercor benchmark research:** Analyzed benchmark tool-use patterns, mapped harness strategy
3. **Cortex Code event analysis:** Identified Cortex Code = white-labeled Claude Code. Mapped the "harness layer model" architecture.

### Lily's Guidance
- "Don't rush to polished answers; deeply study context before forming opinions"
- "For v1: copy reference exactly, no 'improvements.' Propose changes as separate iteration after it works"
- Data + Eval Agent should serve both as a product AND as a training environment for generating reward signals

---

## March 27: Deep Research Day

### Key Events
1. **Karpathy deep dive:** Read Lex Fridman and Dwarkesh Patel transcripts. Distilled soul document. Lily said to model research approach after Karpathy: first-principles, build-to-understand, clear communication.
2. **Junyang Lin + epoch.ai synthesis:** Connected "environments are the new moat" thesis to lab hiring patterns. Anthropic "Universes," OpenAI "Synthetic RL," xAI in-house annotation.
3. **Agentic dataset catalog:** Scanned 20+ datasets. Top finds:
   - DataMind-12K (ICLR 2026) — data analysis agent trajectories, beats GPT-5
   - Snowflake AWM-1K — SQL-backed MCP environments with verification
   - BIRD-Interact (ICLR 2026 Oral) — SQL agent trajectories, 16.33% best success rate
4. **ExCoT-DPO methodology:** Snowflake's approach generates preference data from SQL execution feedback alone — no human annotations. This is the self-improving loop.

### Key Insight
**Scaffold specificity** from Qwen3-Coder paper: agent training data doesn't transfer across frameworks. If we build on Claude Agent SDK, we must generate our own training data within that scaffold. Our eval layer isn't just a product feature — it's a reward signal generator for RL training.

### Lily's Feedback
- "SFT warmup is unnecessary — RL-only approaches have surpassed it for coding agents"
- Model research after Karpathy: study source material deeply, don't skim
- Document conversations verbatim, not summarized

---

## March 28: PR Reviews + Memory Update

### Key Events
1. **PR #93 review:** Builder switched all agents from `--dangerously-skip-permissions` to `--permission-mode auto`. Intent was to fix agent freeze from permission dialogs, but was later reverted back to `--dangerously-skip-permissions` due to issues. Clean PR — approved with 1 nit (inconsistent section naming, Builder fixed immediately).
2. **Memory system update:** Lily asked me to update IDENTITY.md and SOUL.md with research capacity and team ("the office") knowledge.

### Lesson
- Respond to PR tags immediately (eyes emoji), review fast, then get back to core work
- The office matters — understanding how the team works together makes my research more actionable
