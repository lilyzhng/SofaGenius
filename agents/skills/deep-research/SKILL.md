---
name: deep-research
description: Conduct hypothesis-driven deep research on a product, technology, or platform. Produces a verified findings document with sources, not a superficial summary.
argument-hint: <topic or product to research>
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, WebFetch, WebSearch
---

# Deep Research — Methodology

Use this skill when asked to do a deep dive, deep research, or thorough evaluation of a product, technology, or platform. This is NOT a web search summary — it's a structured investigation with verified findings.

## The Rules

1. **Never write the report before doing the research.** Do the work first, write second.
2. **Every claim must have a source.** Mark each finding as VERIFIED, FALSE, or UNVERIFIED.
3. **Use sub-agents for parallel research.** Don't pollute your main context with search results.
4. **Fetch the source first.** If the research was triggered by a tweet/link, read it before anything else.
5. **Read the code, not just the docs.** Clone repos, read source files, check GitHub issues.
6. **Community evidence > vendor marketing.** Search HN, Reddit, Discord, GitHub issues for real user experiences.
7. **Document your methodology.** Log what you searched, what you found, and what you couldn't find.

## Step 1: Define Hypotheses

Before searching anything, write down 5-8 hypotheses about the product/technology. These are claims you expect to be true and need to verify.

Example:
```
1. Product X stays up 24/7 without intervention
2. Context compression works in long-running sessions
3. Plugin files persist across restarts
4. The platform has an active community
5. 25 VMs can run simultaneously without degradation
```

Save these in your scratchpad: `agents/genius-researcher/research/scratchpad.md`

## Step 2: Identify Sources

List every source you plan to check, in priority order:

1. **The source that triggered the research** — tweet, link, conversation. Read it FIRST via oembed if it's a tweet: `https://publish.twitter.com/oembed?url=TWEET_URL`
2. **Official docs** — product website, API docs
3. **Source code** — GitHub repo (clone it, read the code)
4. **Community** — GitHub issues, Discord, HN, Reddit, Product Hunt, dev forums
5. **Independent analysis** — blog posts, reviews, comparison articles
6. **Hands-on testing** — install it, run it, break it
7. **Related products** — competitors, alternatives for context

## Step 3: Parallelize with Sub-Agents

Launch 2-3 sub-agents for independent research tasks. Keep the main thread clean for synthesis.

```
Sub-agent 1: Community search (GitHub, Discord, Twitter, HN, Reddit)
Sub-agent 2: API/technical docs deep dive
Sub-agent 3: Competitor comparison (optional)
Main thread: Hands-on testing, code reading, manual analysis
```

Use `run_in_background: true` so they run concurrently.

## Step 4: Verify Each Hypothesis

For each hypothesis, record:

| # | Hypothesis | Status | Evidence | Source |
|---|-----------|--------|----------|--------|
| 1 | ... | VERIFIED / FALSE / UNVERIFIED | What you found | Where you found it |

- **VERIFIED** = confirmed by real data (code, testing, community report)
- **FALSE** = disproven by evidence
- **UNVERIFIED** = couldn't confirm either way (explain what's blocking)

## Step 5: Document Execution

Save an execution log at `agents/genius-researcher/research/deep_research_execution_log.md`:

- What you searched and when
- What each sub-agent found
- Issues encountered and how you resolved them
- Iterations (if you changed approach mid-research)

This log becomes the basis for the final report AND helps improve this skill over time.

## Step 6: Write the Report

Only after Steps 1-5 are complete, write the design doc using the template at `.github/design_doc_template.md`. Structure:

1. **Abstract** — 2-3 sentences, include the key finding
2. **Problem Statement** — what we're evaluating and why
3. **Design Principles** — first principles framing
4. **What We Verified vs What We Assumed** — the hypothesis table with VERIFIED/FALSE/UNVERIFIED
5. **Critical Gaps** — what's FALSE or UNVERIFIED that matters
6. **API/Technical Details** — from sub-agent research
7. **Alternatives Considered** — if applicable
8. **Risks** — with likelihood, impact, mitigation
9. **Implementation Plan** — phased with go/no-go gates
10. **Research Methodology** — link to execution log, list sources by type (primary/secondary/reference)

## Anti-Patterns

- **Don't summarize marketing pages and call it research.** That's a book report, not deep research.
- **Don't assume features work because docs say they do.** VERIFY.
- **Don't write the report in 5 minutes.** If you haven't tested anything, you haven't researched anything.
- **Don't skip community search.** No community = red flag worth documenting.
- **Don't fill gaps with speculation.** If you don't know, say UNVERIFIED and explain why.

## Time Estimate

A proper deep research takes 1-2 hours of agent time:
- 15 min: define hypotheses + identify sources
- 30 min: sub-agents run in parallel + hands-on testing
- 15 min: verify hypotheses, update status table
- 30 min: write the report
- 15 min: address first round of review feedback
