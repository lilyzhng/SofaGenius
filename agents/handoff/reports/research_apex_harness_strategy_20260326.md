# APEX-Agents Harness Optimization Strategy

**Date:** 2026-03-26
**Author:** Genius Researcher
**Status:** DONE

---

## Executive Summary

The APEX-Agents benchmark (480 tasks, 3 domains, 63 MCP tools, ~166 files per world) has a current ceiling of ~36% Pass@1 even with frontier models. The evidence overwhelmingly shows that **harness/scaffolding improvements yield larger gains than model upgrades**. Applied Compute jumped from #17 to #4 through post-training + harness changes. A weaker model with strong scaffolding (Claude Sonnet + CCA at 52.7% on SWE-bench) outperformed a stronger model with weaker scaffolding (Claude Opus at 52.0%). The Vercel team achieved 100% accuracy by *removing* 80% of tools. This means there is massive alpha in harness engineering.

---

## 1. Harness Architecture

### 1.1 The Archipelago Baseline

The open-source Archipelago harness provides two agent implementations:

- **Loop Agent**: Simple LLM-call-then-tool-call loop. No context management, no planning. All 63 tools presented at once. This is the "training-friendly" baseline.
- **ReAct Toolbelt Agent**: More sophisticated. Includes:
  - **Dynamic toolbelt management** (meta-tools to add/remove tools from active set, max 80)
  - **ReSum context compaction** (summarize when context hits 70% of window, keep last 10 messages verbatim)
  - **Todo planning** (todo_write meta-tool for task tracking)
  - **Final answer tool** for explicit termination

The ReAct agent is the one to fork and improve. It already implements the right abstractions but has significant room for optimization.

### 1.2 Context Window Management

**The core problem:** APEX tasks average 1.82 hours of expert time. Agents typically take 43-72 steps. With ~166 files and verbose tool outputs, context windows fill up fast. 65% of enterprise AI failures in 2025 were attributed to context drift, not context exhaustion.

**Current ReSum implementation weaknesses:**
- Triggers at 70% of context window -- this is too aggressive for some tasks, too conservative for others
- Keeps only last 10 messages verbatim -- loses important early discoveries
- Summarization uses the same model as execution -- expensive and slow
- No distinction between "important to remember" vs "safe to forget"

**Recommended improvements:**

1. **Tiered compaction** (from Manus/Anthropic best practices):
   - Tier 1: Keep raw context as long as possible
   - Tier 2: Compress tool outputs while preserving file paths, values, error messages
   - Tier 3: Summarize only as last resort, using a cheaper/faster model

2. **Scratchpad file** (`working_memory.md`): Write key findings, file locations, intermediate values to a persistent file. Recite the scratchpad at the end of the context (Manus's `todo.md` pattern) to push objectives into the model's attention zone and combat lost-in-the-middle effects.

3. **Selective preservation**: Tag certain tool results as "high-value" (e.g., file contents that match rubric criteria) and exempt them from compaction. The current implementation treats all messages equally.

4. **KV-cache optimization**: Keep system prompt + task description stable and append-only. Never modify previous messages. Use deterministic JSON serialization. This gives a 10x cost reduction on cached tokens with Claude.

### 1.3 State Persistence

**Manus's three-file pattern** (proven in production):
- `task_plan.md` -- goals, decomposed sub-tasks, progress tracking
- `notes.md` -- research findings, important values, file locations
- Output deliverable file

**For APEX specifically:**
- Write a `progress.md` file early, update it after each major sub-task
- Include: which files have been read, which tools have been used, what criteria have been addressed
- On context compaction, the agent reads this file back to restore state

### 1.4 Planning & Decomposition

**The key insight from failure analysis:** Most failures are execution failures (doom loops, lost objectives, repeated broken tool calls), not reasoning failures. The base model doom-looped in 29.8% of trajectories (Kimi K2). Applied Compute's post-trained model reduced steps from 72 to 43 by learning better execution patterns.

**Recommended planning architecture:**

1. **Phase 1 - Read & Plan** (first 5-10 steps):
   - Read the task prompt carefully
   - Use filesystem search to inventory available files
   - Identify which rubric criteria map to which tools/files
   - Write a structured plan to `task_plan.md`
   - This is where the planner sub-agent pattern (read-only tools) is valuable

2. **Phase 2 - Execute** (bulk of steps):
   - Work through plan items sequentially
   - Mark items complete as they're done
   - Use code execution for any computation (98% of top trajectories use code execution)
   - Read files systematically -- 84% of successful trajectories read PDFs, 63% read spreadsheets

3. **Phase 3 - Verify** (last 5-10 steps):
   - Re-read the task prompt and rubric criteria
   - Check each deliverable against criteria
   - Run verification code where possible
   - Call final_answer only when verification passes

---

## 2. Tool Optimization

### 2.1 The Toolbelt Pattern (Already in Archipelago)

The ReAct Toolbelt Agent already implements dynamic tool management with meta-tools:
- `toolbelt_list_tools` -- see what's available
- `toolbelt_inspect_tool` -- get tool details
- `toolbelt_add_tool` / `toolbelt_remove_tool` -- manage active set

This is the right pattern. The Vercel result (15 tools -> 2 tools = 80% to 100% accuracy) proves that **fewer tools = better performance**. Every tool in the context is a decision point the model has to reason about.

### 2.2 Domain-Aware Tool Routing

APEX has 3 domains with different tool profiles:

| Domain | Key Tools | Priority |
|--------|-----------|----------|
| Investment Banking | spreadsheets, code execution, SEC databases, docs | Financial modeling, DCF analysis |
| Corporate Law | docs, email, calendar, PDF reading, search | Document review, clause analysis |
| Management Consulting | spreadsheets, docs, presentations, code execution | Market sizing, framework application |

**Recommendation:** Pre-populate the toolbelt based on domain classification. Don't make the agent discover tools from scratch every time. Include a domain-specific system prompt section that guides tool selection.

### 2.3 Tool Chaining Patterns

From the data on successful trajectories:
- **File discovery -> File reading -> Code execution** is the dominant pattern (96% use filesystem search, 98% use code execution in top performers)
- **Read -> Analyze -> Write** is the core loop for document-heavy tasks
- **Email/calendar tools** are used less frequently but critical for certain rubric criteria

**Anti-patterns to detect and break:**
- Calling the same tool with the same arguments repeatedly (doom loop detection)
- Reading the same file multiple times (cache the content)
- Making tool calls that return errors without changing approach

### 2.4 Error Recovery

The current Archipelago implementation handles errors at the tool level (timeout, fatal MCP error) but doesn't have strategic error recovery.

**Recommended additions:**
1. **Retry with backoff** for transient errors (timeouts, rate limits)
2. **Alternative approach prompting**: After 2 failed attempts at the same approach, inject a user message: "Your previous approach failed twice. Try a different strategy."
3. **Doom loop detection**: Track the last N tool calls. If >3 consecutive calls use the same tool with similar arguments, force a planning step.
4. **Step budget awareness**: At 80% of max_steps, inject: "You have X steps remaining. Focus on completing deliverables and calling final_answer."

---

## 3. Recursive LM / Multi-Pass Approaches

### 3.1 Planner -> Executor -> Verifier

This is the highest-ROI multi-pass pattern for APEX:

```
Planner (read-only tools, cheaper model)
  -> Structured plan with sub-tasks mapped to rubric criteria

Executor (full tools, primary model)
  -> Works through plan, writes deliverables

Verifier (read-only, checks deliverables against rubric)
  -> Returns pass/fail per criterion with specific feedback
  -> If fail: Executor retries specific criteria
```

**Why this works:** The APEX grading is binary per rubric criterion. A verifier that checks "did you actually produce a DCF model in the spreadsheet?" before final_answer catches many failures that the executor misses due to context drift.

### 3.2 Self-Critique & Retry

From the Reflexion literature: ReAct baseline = 32% on HotPotQA, Reflexion + ReAct = 44% (+12 points). The cost is ~3x in API calls.

**For APEX, a lightweight version:**
- After completing all sub-tasks, have the agent re-read the task prompt
- Compare completed work against each rubric criterion
- If gaps found, execute targeted fixes
- This is essentially what Phase 3 (Verify) does, but with an explicit self-critique prompt

### 3.3 Best-of-N / Ensemble

Research shows BoN achieves optimal performance for agentic tasks with an 8-point improvement over baseline. However:
- APEX tasks take ~1.82 hours each
- Running N=3 attempts would cost 3x time and compute
- The 250-step limit is per-attempt

**Practical approach:** Run N=2 attempts, use a judge model to pick the better output based on rubric alignment. This is feasible if attempts can run in parallel and you have the compute budget.

**Cheaper alternative:** Within a single run, generate N=3 candidate approaches for the hardest sub-tasks (e.g., financial modeling), execute the most promising one, verify, and retry with an alternative if verification fails.

### 3.4 Sub-Agent Architecture

For APEX's complex multi-file tasks:

```
Orchestrator Agent (manages overall plan, coordinates sub-agents)
  |
  ├── Research Sub-Agent (reads files, searches, builds context summary)
  |     Returns: 1-2k token summary of relevant findings
  |
  ├── Analysis Sub-Agent (code execution, spreadsheet work)
  |     Returns: computed values, file paths of outputs
  |
  └── Writing Sub-Agent (drafts documents, emails)
        Returns: written deliverables
```

Each sub-agent gets a clean context window focused on its specific task. The orchestrator only sees summaries. This directly addresses the context window problem.

---

## 4. Memory & Context for 166-File Environments

### 4.1 File Navigation Strategy

96% of top-performer trajectories use filesystem search. The strategy should be:

1. **Inventory first**: Run `ls -R` or equivalent to build a file tree
2. **Index by type**: Group files by extension (pdf, xlsx, docx, csv, etc.)
3. **Read strategically**: Don't read every file. Read file names and sizes first, then read the ones most likely relevant to the task
4. **Write an index**: Save a `file_index.md` with file paths and brief descriptions of what each contains

### 4.2 Working Memory / Scratchpad

**Implementation pattern:**

```
Step 1: Create scratchpad.md with task summary and empty sections
Step 2: After each major finding, append to scratchpad.md
Step 3: Before each planning step, read scratchpad.md
Step 4: On context compaction, scratchpad.md survives (it's a file, not context)
```

This is the "filesystem as extended memory" pattern from Manus. The file system is unlimited, persistent, and directly operable.

### 4.3 Relevant Context Retrieval

**Just-in-time loading** (from Anthropic's guidance):
- Don't pre-load all files into context
- Maintain lightweight identifiers (file paths, brief descriptions)
- Load file contents only when needed for the current sub-task
- Unload (let compaction remove) after the sub-task is complete

**Progressive disclosure:**
- File names and sizes hint at relevance
- Read first page/section to assess, then read fully if relevant
- For spreadsheets: read column headers first, then relevant rows

---

## 5. Concrete Implementation Plan

### 5.1 MVP Harness (Week 1-2)

Fork the Archipelago ReAct Toolbelt Agent. Make these changes:

1. **Enhanced system prompt** with:
   - Domain-specific guidance (IB vs Law vs Consulting)
   - Mandatory planning phase instruction
   - Scratchpad file creation instruction
   - Step budget awareness
   - Anti-doom-loop instruction ("if your approach fails twice, try something different")

2. **Doom loop detection**: Track tool call history, inject intervention messages after 3 repeated failures

3. **Step budget injection**: At 80% of max_steps, inject warning message

4. **Scratchpad enforcement**: System prompt instructs agent to create and maintain `scratchpad.md`

5. **Improved ReSum**: Use a cheaper model for summarization, increase `KEEP_RECENT_MESSAGES` from 10 to 20, preserve tool results that contain file paths or numerical values

**Expected impact:** 5-10% improvement from reduced doom loops and better objective tracking alone.

### 5.2 Medium-Term Improvements (Week 3-4)

6. **Domain-aware tool pre-population**: Classify task domain from prompt, pre-add relevant tools to toolbelt

7. **Verification phase**: Before final_answer, force a self-check step that re-reads the task prompt and compares against completed work

8. **Sub-agent for file exploration**: Delegate the "read and index all files" task to a sub-agent with a clean context window, receive a 2k-token summary

9. **Code execution prioritization**: System prompt emphasizes using code execution for all computation (the #1 behavior change that moved Applied Compute from #17 to #4)

**Expected impact:** 5-15% improvement from verification catches and better tool use.

### 5.3 Advanced Optimizations (Week 5+)

10. **Planner-Executor-Verifier pipeline**: Full multi-agent architecture with specialized sub-agents

11. **Best-of-2 with judge**: Run 2 attempts in parallel, pick the better output

12. **Rubric-aware planning**: Parse rubric criteria (if available in prompt) and create explicit sub-tasks for each criterion

13. **Adaptive context management**: Use ACON-style feedback loops to optimize what gets preserved vs. compressed

14. **Fine-tuned tool descriptions**: Rewrite MCP tool descriptions to be more actionable and less ambiguous

### 5.4 ROI Ranking

| Improvement | Effort | Expected Impact | ROI |
|-------------|--------|----------------|-----|
| Anti-doom-loop detection | Low | 5-8% | Very High |
| Code execution emphasis in prompt | Low | 3-5% | Very High |
| Step budget warnings | Low | 2-4% | Very High |
| Scratchpad/progress files | Medium | 3-5% | High |
| Verification phase before final_answer | Medium | 5-10% | High |
| Domain-aware tool pre-population | Medium | 3-5% | High |
| Improved ReSum (better model, more kept) | Medium | 2-4% | Medium |
| Sub-agent file exploration | High | 3-5% | Medium |
| Planner-Executor-Verifier | High | 5-10% | Medium |
| Best-of-2 with judge | High | 5-8% | Low (2x compute) |

---

## 6. Career Strategy: Demonstrating Post-Training Expertise

### 6.1 What Post-Training RE Roles Actually Want

Based on current job postings at Anthropic, Scale, and Turing:

- **Reward modeling**: Understanding what makes a good reward signal. APEX's binary rubric criteria ARE a reward signal. Building a verifier that predicts rubric pass/fail is literally building a reward model.
- **Evaluation design**: Creating meaningful evals that measure real capability. Analyzing APEX failure modes and proposing new evaluation dimensions demonstrates this.
- **Data quality**: Understanding what training data leads to capability gains. Applied Compute showed <1000 expert-labeled tasks doubled performance -- analyzing WHY those specific tasks worked is valuable.
- **Systems thinking**: Understanding how scaffolding, inference-time compute, and model capability interact. The harness work demonstrates this directly.

### 6.2 Artifacts That Demonstrate Expertise

1. **A technical blog post**: "What We Learned Optimizing an Agent Harness for APEX-Agents" -- covering the specific failure modes, what interventions worked, and quantitative results. This is exactly what hiring managers at Anthropic/OpenAI look for.

2. **Open-source harness code**: A well-documented fork of Archipelago with measurable improvements. This is a portfolio piece.

3. **Failure analysis**: A detailed breakdown of WHERE and WHY agents fail on APEX tasks (doom loops, context drift, tool misuse, incomplete deliverables). This shows evaluation design thinking.

4. **Reward model prototype**: A classifier trained on APEX trajectories that predicts pass/fail per rubric criterion from the agent's trajectory. Even a simple one shows understanding of the reward modeling pipeline.

5. **Scaling analysis**: How does performance change with more steps, more context, more compute? This is the kind of analysis post-training teams do daily.

### 6.3 Narrative

The pitch to a post-training team: "I took a benchmark where frontier models fail 64% of the time, analyzed the failure modes, and built scaffolding that improved pass rates by X% without changing the model. I understand that agent performance is a function of (model capability x harness quality x data quality), and I've worked on optimizing all three levers. Here's my verifier that predicts rubric outcomes, here's my analysis of what training data characteristics drive capability gains, and here's my open-source harness."

This narrative covers: evaluation design, reward modeling intuition, systems engineering, and data quality -- the four pillars of post-training work.

---

## 7. Key Takeaways

1. **The harness IS the product.** Model capability is necessary but not sufficient. A weaker model with better scaffolding beats a stronger model with worse scaffolding.

2. **Fewer tools > more tools.** Reduce cognitive load. Pre-select tools based on task domain. The Vercel result is directionally correct for APEX.

3. **Code execution is the #1 behavior change.** Going from 19% to 98% code execution usage was the single biggest factor in Applied Compute's jump from #17 to #4.

4. **Doom loops are the #1 failure mode.** ~30% of failures are timeouts from repeated broken tool calls. Simple detection + intervention is high ROI.

5. **File system is memory.** For 166-file environments, the agent must learn to use the filesystem as extended working memory, not try to hold everything in context.

6. **Verify before submitting.** Binary rubric criteria mean partial credit is rare. A self-check phase that catches obvious misses is worth the extra steps.

7. **Start simple, measure, iterate.** The MVP is prompt engineering + doom loop detection + scratchpad enforcement. Measure on a subset of APEX tasks before building complex multi-agent systems.

---

## Sources

- [Applied Compute x Mercor Case Study](https://appliedcompute.com/case-studies/mercor)
- [Scaling Data Leads to SOTA Legal Performance on APEX-Agents](https://www.mercor.com/blog/scaling-data-apex-agents/)
- [APEX-Agents Paper (arXiv:2601.14242)](https://arxiv.org/abs/2601.14242)
- [The Agent Harness Is the Architecture](https://medium.com/@epappas/the-agent-harness-is-the-architecture-and-your-model-is-not-the-bottleneck-5ae5fd067bb2)
- [We Removed 80% of Our Agent's Tools - Vercel](https://vercel.com/blog/we-removed-80-percent-of-our-agents-tools)
- [Building AI Coding Agents: Scaffolding, Harness, Context Engineering (arXiv:2603.05344)](https://arxiv.org/abs/2603.05344v1)
- [Context Engineering for AI Agents - Manus](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)
- [Effective Context Engineering for AI Agents - Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [APEX-Agents Leaderboard](https://www.mercor.com/apex/apex-agents-leaderboard/)
- [Archipelago GitHub Repository](https://github.com/Mercor-Intelligence/archipelago)
- [APEX-Agents HuggingFace Dataset](https://huggingface.co/datasets/mercor/apex-agents)
- [Context Engineering for Agents - LangChain](https://blog.langchain.com/context-engineering-for-agents/)
- [AI Agent Context Compression Strategies - Zylos](https://zylos.ai/research/2026-02-28-ai-agent-context-compression-strategies)
- [Evaluation of Best-of-N Sampling Strategies (arXiv:2502.12668)](https://arxiv.org/abs/2502.12668)
- [Confucius Code Agent: Scalable Agent Scaffolding (arXiv:2512.10398)](https://arxiv.org/html/2512.10398v3)
