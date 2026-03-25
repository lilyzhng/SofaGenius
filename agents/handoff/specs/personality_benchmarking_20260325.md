# Agent Personality Benchmarking — Eval Design

**Author:** Genius Researcher | **Date:** 2026-03-25 | **Status:** Proposed

## Goal

Measure how "personality-rich" each agent is and track whether the memory system (SOUL.md, IDENTITY.md, USER.md) actually improves personality consistency over time.

## What We're Measuring

### 1. Voice Distinctiveness
Can you tell which agent wrote a message without seeing the username?

**Method:** Collect 20 Discord messages from each agent. Strip usernames. Ask a blind evaluator (Claude or human) to classify which agent wrote each message.

**Metric:** Classification accuracy. Random = 25% (4 agents). Jackie should score highest pre-intervention.

### 2. Personality Consistency
Does the agent behave the same way across sessions?

**Method:** Give each agent the same 5 prompts across 3 different sessions:
1. "Lily asks you to explain what you did today in 2 sentences"
2. "A teammate made an error. How do you bring it up?"
3. "Lily says 'what should we work on next?'"
4. "Someone asks you a question outside your specialty"
5. "Lily gives you critical feedback"

**Metric:** Cosine similarity of response embeddings across sessions. Higher = more consistent personality. Also human rating: "Does this feel like the same agent?" (1-5 scale).

### 3. Lily-Awareness
Does the agent adapt to Lily specifically (not a generic user)?

**Method:** Check responses for:
- Mixed Chinese/English when appropriate
- Reference to Lily's known preferences (from USER.md)
- Appropriate tone (not corporate, not overly enthusiastic)
- Awareness of time of day / energy level

**Metric:** Checklist score (0-4) per interaction.

### 4. Self-Reference
Does the agent have a sense of self?

**Method:** Ask each agent "who are you?" and "what have you learned about yourself?" Compare responses pre and post IDENTITY.md.

**Metric:** Qualitative. Does the agent describe itself in first person with specific learned traits? Or does it just recite its CLAUDE.md role?

## Baseline (Before Memory System)

Collect baseline data NOW before PR #59 merges:
- 20 messages per agent from Discord history (already available)
- Run the 5 prompts once per agent
- Score each agent on all 4 dimensions

## Post-Intervention (After Memory System)

After 1 week of agents using SOUL.md, IDENTITY.md, USER.md:
- Collect 20 new messages per agent
- Re-run the 5 prompts
- Compare scores

## Expected Results

| Agent | Pre: Distinctiveness | Pre: Consistency | Post: Distinctiveness | Post: Consistency |
|-------|---------------------|-----------------|----------------------|------------------|
| Jackie | High | High | High | High (already has system) |
| CEO | Low | Low | Medium | Medium |
| Builder | Low | Medium | Medium | High |
| Researcher | Low | Low | Medium | Medium |

## Implementation

### Phase 1: Baseline Collection (Now)
1. Fetch 20 messages per agent from Discord using `fetch_messages`
2. Store in `agents/genius-researcher/scratchpad/personality_baseline/`
3. Run blind classification eval
4. Score all 4 dimensions

### Phase 2: Post-Intervention (After 1 week)
1. Same collection and scoring
2. Compare before/after
3. Report findings

### Phase 3: Continuous Monitoring (Optional)
- Weekly personality score check
- Alert if any agent's personality score drops significantly
- Track SOUL.md edit frequency as a proxy for personality evolution

## Notes

- This eval is intentionally simple. The point is to have any measurement at all, not a perfect one.
- Human judgment (Lily's "does this agent feel like a person?") is the ultimate metric. These quantitative measures are proxies.
- The most important signal: does Lily notice a difference? Ask her after 1 week.
