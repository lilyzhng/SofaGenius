---
name: auto-research
description: Run parallel deep research on a topic. Spawns sub-agents, collects findings, produces a verified report.
argument-hint: <topic> [optional: --depth shallow|medium|deep]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, WebSearch, WebFetch
---

# Auto-Research Pipeline

Takes a research topic, decomposes it into parallel research tracks, spawns sub-agents, and compiles a verified findings document.

## How It Works

### 1. Decompose the topic

Break the research question into 3-5 parallel research tracks. Each track should be:
- Independent (can be researched in parallel)
- Specific (clear scope, not vague)
- Verifiable (findings can be fact-checked)

Example for "agentic training datasets":
- Track 1: HuggingFace dataset discovery (tool-calling, multi-turn, RL)
- Track 2: GitHub repos and frameworks (synthetic data generation, benchmarks)
- Track 3: Recent papers and SOTA results (2025-2026)

### 2. Spawn parallel research agents

For each track, launch a background Agent with:
- Clear scope: what to search for
- Output format: structured findings with sources
- Verification requirement: every claim needs a source URL

```
Agent(
  description="Research track N",
  prompt="Research [specific scope]. For each finding, include: name, URL, size, license, relevance (HIGH/MEDIUM/LOW), and source link. Return at least N items.",
  run_in_background=true
)
```

### 3. Collect and deduplicate

When all agents complete:
- Merge findings across tracks
- Deduplicate (same dataset/tool found by multiple agents)
- Resolve conflicts (different agents report different stats)
- Verify key claims by spot-checking source URLs

### 4. Compile the report

Save to `agents/handoff/reports/research_{topic}_{date}.md`:

```markdown
# {Topic} — Research Report

**Author:** Genius Researcher | **Date:** {date} | **Status:** Complete

## Executive Summary
{2-3 sentence overview of key findings}

## Tier 1: High Relevance
{Table format: Name | Size | License | URL | Relevance | Best For}

## Tier 2: Medium Relevance
{Same format}

## Tier 3: Supplementary
{Same format}

## Gap Analysis
{What's missing? What needs to be synthesized?}

## Recommended Actions
{Concrete next steps}

## Sources
{All URLs referenced}
```

### 5. Post findings

- Update task tracker
- Post summary in relevant Discord thread
- Tag Growth if findings affect strategy

## Depth Levels

- **shallow** (default): 2 parallel agents, ~15 min, ~15 findings
- **medium**: 3-4 parallel agents, ~30 min, ~30 findings
- **deep**: 5+ parallel agents, ~60 min, ~50+ findings (what we did for agentic datasets tonight)

## When to Use

- Growth assigns a research topic
- Data discovery for new domains
- Competitive analysis
- Technology evaluation
- Any research that benefits from parallel exploration

## Anti-Patterns

- Don't run auto-research for simple questions (just search directly)
- Don't spawn more than 5 agents (diminishing returns, context pollution)
- Don't skip verification — every claim needs a source
- Don't produce reports without a gap analysis — knowing what's missing is as valuable as what's found
