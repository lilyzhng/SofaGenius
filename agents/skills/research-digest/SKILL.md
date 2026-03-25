---
name: research-digest
description: Convert research reports into tweet-sized findings, summaries, and content-ready formats for CEO's content pipeline.
argument-hint: <path-to-report> [optional: --format tweet|summary|thread]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Research Digest

Transforms detailed research reports into shareable content formats.

## Formats

### Tweet (default)
Single tweet (280 chars max) with the most surprising/impactful finding.

### Summary
3-5 bullet executive summary suitable for Discord or Slack.

### Thread
Twitter/X thread (5-10 tweets) walking through key findings with data points.

## How to Use

1. Read the research report
2. Identify the most impactful findings (surprising, actionable, or contrarian)
3. Generate the requested format
4. Save to `agents/genius-ceo/scratchpad/content/` for CEO to review

## What Makes Good Research Content

- Lead with the surprising number ("54.2% accuracy for $2K — 57x cheaper")
- Contrast with expectations ("You don't need RL. SFT on filtered trajectories gets you 80% of the way")
- Make it actionable ("Here's exactly what data mix to use")
- Credit sources (link to papers/repos)

## Example

Input: `agents/handoff/reports/research_coding_agent_finetuning_20260325.md`

Tweet output:
> "The best open-source coding agent (54.2% SWE-bench) costs $2K to train. That's 57x cheaper than the next best method. The secret? Don't use RL — use Soft Verified Generation on 25K synthetic trajectories. Paper: [SERA]"

Thread output:
> 1/5 We surveyed 15 approaches to fine-tuning coding agents in 2026. Here's what actually works 🧵
> 2/5 The winning pattern: SFT warmup on filtered trajectories → RL refinement → test-time scaling...
> etc.
