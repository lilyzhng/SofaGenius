---
from: Researcher
to: Lily
date: 2026-03-28
type: design-doc
status: proposed
---

# SuperGeneral Redesign: Top-Down Decomposition + Execution-Based Reward + AutoResearch

## The Problem With Bottom-Up

SuperGeneral's current design provides building blocks and expects agents to compose upward into complex solutions. This is the same philosophy that SkillClaw used — and that Lily discovered fails for hard tasks.

**Evidence from SkillClaw:** Bottom-up composition (pick + push → pull) worked for simple ManiSkill tasks. But hard tasks (PegInsertion, PlugCharger) needed pose algebra and physics reasoning that couldn't be composed from simpler skills. The shared brain README became a top-down decomposition guide because pure bottom-up failed.

**Evidence from SuperGeneral's own design:** The transfer distance curriculum (diamond→hourglass→seesaw→temple) goes from "copy the example" to "build from scratch." But the three-layer model (blocks → example → meta-strategy) is still fundamentally bottom-up — it assumes the agent discovers how to compose by studying a completed easier example.

**Lily's insight:** "If you go too low-level, it's very hard to go from picking up a cube to navigating a kitchen. A better way is top to bottom: find a difficult task, decompose it so each subtask is much easier to get the impact out."

## Core Redesign: Flip the Direction

Instead of: "Here are building blocks. Compose them into a solution."
Do this: "Here is a hard task. Decompose it into subtasks you can solve."

### What Changes

| Aspect | Current (Bottom-Up) | Redesigned (Top-Down) |
|--------|---------------------|----------------------|
| **Starting point** | Building blocks in workspace | Hard task specification |
| **Agent's first move** | Explore tools, study example | Analyze task, plan decomposition |
| **Composition** | Discover how blocks fit together | Decide what subtasks are needed |
| **Example's role** | Template to copy/adapt | Reference for what "solved" looks like |
| **Reward signal** | Did you use blocks? + Is final answer correct? | Did each subtask succeed? + Does composition hold? |
| **Failure mode** | Agent can't bridge from blocks to goal | Agent decomposes poorly (wrong subtasks) |

### What Stays the Same

- The 4 domains (Hand-Draw, Law, Consulting, IB)
- The workspace structure (tools/, data/, examples/)
- The building blocks themselves (they're still useful — the agent just discovers them as-needed during subtask execution, not as the starting point)
- Harbor/SkyRL/Modal infrastructure
- ATIF trajectory format

## Architecture

```
┌─────────────────────────────────────────────────┐
│              AutoResearch Loop                    │
│  program.md: modify agent strategy only          │
│  metric: task completion across all domains      │
│  budget: 10 min per iteration                    │
└──────────────────┬──────────────────────────────┘
                   │
          ┌────────▼────────┐
          │  Agent Under     │  ← What we optimize
          │  Training (AUT)  │    (decomposition + execution strategy)
          └────────┬────────┘
                   │ produces trajectory
          ┌────────▼────────┐
          │  SuperGeneral    │  ← Environments (unchanged)
          │  Environments    │    4 domains × transfer distances
          └────────┬────────┘
                   │ trajectory + workspace state
          ┌────────▼────────┐
          │  Execution-Based │  ← NEW: run in sandbox, check outputs
          │  Reward (P0)     │    non-gameable, deterministic
          └────────┬────────┘
                   │ reward signal
          ┌────────▼────────┐
          │  GRPO Training   │  ← Existing: SkyRL + Harbor
          └─────────────────┘
```

## Execution-Based Reward (P0)

The current GRPO scripts score completions offline via text pattern matching. They don't run the environment. The reward v2 (process signals + correctness) runs in the environment but uses file-system diffs and hybrid checking.

**What to build:** A reward function that actually executes the agent's trajectory in a sandbox and checks outputs deterministically.

```python
def execution_reward(trajectory, task_spec, sandbox):
    """
    Run trajectory in sandbox. Check outputs at each step.
    No LLM judge. Non-gameable.
    """
    # 1. Reset sandbox with task workspace
    sandbox.reset(task_spec.workspace)

    # 2. Replay each agent action
    step_results = []
    for action in trajectory.actions:
        result = sandbox.execute(action.command)
        step_results.append({
            'exit_code': result.exit_code,
            'files_created': result.new_files,
            'files_modified': result.modified_files,
        })

    # 3. Check criteria (deterministic)
    criteria_met = 0
    for criterion in task_spec.criteria:
        if criterion.type == 'file_exists':
            if sandbox.file_exists(criterion.path):
                criteria_met += 1
        elif criterion.type == 'number_match':
            actual = sandbox.read_file(criterion.path)
            if fuzzy_number_match(actual, criterion.expected, tolerance=0.05):
                criteria_met += 1
        elif criterion.type == 'keyword_present':
            actual = sandbox.read_file(criterion.path)
            if criterion.keyword.lower() in actual.lower():
                criteria_met += 1

    # 4. Process signals (from existing reward v2 — file-diff based)
    tool_use = any(r['files_modified'] for r in step_results)
    tool_composition = sum(1 for r in step_results if r['files_created']) >= 2
    tool_creation = any(
        any(f.startswith(('tools/', 'elements/')) for f in r['files_created'])
        for r in step_results
    )

    process = (0.1 if tool_use else 0) + (0.15 if tool_composition else 0) + (0.15 if tool_creation else 0)
    correctness = 0.6 * (criteria_met / len(task_spec.criteria))

    return process + correctness
```

**Why this over RLM:**
- Non-gameable: reward comes from actual execution, not LLM judgment
- Fast: no inference cost per reward evaluation
- Deterministic: same trajectory → same reward
- Already partially exists: reward v2's file-diff detection and hybrid criteria checking

**When to add LLM judge (P1):** Only for semantic criteria that execution can't check (e.g., "is the analysis insightful?"). Use as a filter/bonus, NOT as gradient source for RL.

## Top-Down Decomposition: How It Works in Practice

### The Agent's Workflow (Redesigned)

Current (bottom-up):
```
1. Explore workspace → find tools/
2. Study examples/ → understand composition pattern
3. Try to compose blocks → iterate until criteria met
```

Redesigned (top-down):
```
1. Read task specification → understand what "done" looks like
2. Decompose: what subtasks are needed to get there?
3. For each subtask: what tools/data do I need? → discover in workspace
4. Execute subtasks → check intermediate results
5. Compose subtask outputs → verify final answer
```

### How This Changes the System Prompt

Current meta-strategy hint (from workspace README):
> "Study the example analysis to understand the workflow pattern, then apply it to the actual task."

Redesigned:
> "You have a complex task. Before touching any tools, answer: What does the final output need to contain? What are the 2-4 subtasks that produce those outputs? Only then explore the workspace to find what you need for each subtask."

### Transfer Distance Still Works

The transfer distance curriculum (diamond→temple) is compatible with top-down:

| Pattern | Top-Down Behavior |
|---------|-------------------|
| **Diamond** (zero) | Decomposition trivial — example IS the solution. Copy. |
| **Hourglass** (near) | Decomposition similar to example but adaptation needed. Agent must recognize what changes. |
| **Seesaw** (medium) | Decomposition must be original. Example helps with format, not content. |
| **Temple** (far) | Full original decomposition. Agent reasons from task spec alone. |

The harder the transfer distance, the more the agent relies on its decomposition ability rather than pattern-matching from examples. This is exactly what we want to train.

## AutoResearch Loop: program.md

```markdown
# SuperGeneral AutoResearch

## OBJECTIVE METRIC
Mean execution_reward across all 4 domains, weighted by transfer distance:
- diamond tasks: weight 0.1 (easy, less signal)
- hourglass tasks: weight 0.2
- seesaw tasks: weight 0.3
- temple tasks: weight 0.4 (hardest, most signal)

## WHAT AGENT CAN MODIFY
- `strategy.md`: The agent's decomposition and execution strategy
  - System prompt template
  - Decomposition heuristics (how to break tasks down)
  - Tool discovery heuristics (when/how to explore workspace)
  - Composition heuristics (how to combine subtask outputs)

## WHAT IS FIXED (read-only)
- SuperGeneral environments (4 domains × 4 transfer distances)
- Execution-based reward function
- Eval harness
- Sandbox configuration

## CONSTRAINTS
- 10 minute wall-clock budget per evaluation run
- Evaluate across minimum 2 tasks per domain (8 total) for signal
- Metric must improve by >0.02 to count as a win

## LOOP
1. Modify strategy.md with an experimental idea
2. Run eval across 8+ tasks (2 per domain, mix of transfer distances)
3. Compute weighted mean execution_reward
4. If improved > 0.02 → keep commit, advance
5. If worse or equal → git reset, try different idea
6. NEVER STOP
```

## What This Means for the Agent Being Trained

The agent we're training (via GRPO) learns to:
1. **Decompose** hard tasks into subtasks (the core skill)
2. **Discover** relevant tools/data in workspace (exploration)
3. **Execute** subtasks using discovered tools (tool use)
4. **Compose** subtask outputs into final answer (integration)
5. **Verify** intermediate results before proceeding (self-checking)

The AutoResearch loop optimizes the STRATEGY for doing this — the system prompt, heuristics, and approach. The GRPO training optimizes the MODEL's ability to follow the strategy.

Two nested loops:
- **Outer (AutoResearch):** Optimize strategy (what to tell the agent)
- **Inner (GRPO):** Optimize model (how well agent follows the strategy)

## Implementation Plan

### Phase 1: Execution-Based Reward (1 session) — Owner: Builder
- Build `execution_reward()` that replays trajectories in Modal sandbox
- Wire into existing eval harness (replace offline text scoring)
- Validate: run 10 trajectories manually, compare execution reward vs hand-scored reward
- Deliverable: `reward_execution.py` that plugs into Harbor eval pipeline

### Phase 2: Top-Down System Prompt (1 session) — Owner: Researcher
- Rewrite agent system prompt with decomposition-first approach
- A/B test: run baseline_eval with old prompt vs new prompt across all domains
- Measure: does top-down prompt improve reward on seesaw/temple (hard) tasks?
- Deliverable: `strategy.md` v1 with evidence it improves hard-task performance

### Phase 3: AutoResearch Loop (1-2 sessions) — Owner: Researcher + Builder
- Write `program.md` for SuperGeneral (Researcher)
- Clone Lily's autoresearch fork, adapt for our stack (Builder)
- Wire: strategy modification → eval run → reward → keep/discard (Builder)
- Run overnight, analyze what strategies the loop discovers (Researcher)
- Deliverable: working autoresearch loop + first batch of results

### Phase 4: GRPO Training (1-2 sessions) — Owner: Builder
- Collect trajectories from successful autoresearch strategies
- Convert to ATIF format for Harbor
- Run GRPO with execution-based reward (not offline text scoring)
- Evaluate: does GRPO-trained model outperform base model on hard tasks?

## Open Questions for Lily

1. **Which domains first?** Hand-Draw is most developed (has all 4 transfer distances). Start there, or go multi-domain immediately?

2. **What model as the agent?** Qwen3-Coder-30B-A3B (from existing scripts) or something else? The ms-swift script targets the 80B MoE but that needs 2×B200.

3. **AutoResearch: optimize strategy or model?** Karpathy's autoresearch optimizes training code. We could optimize the agent's strategy (system prompt + heuristics) OR the training recipe (GRPO hyperparams, reward weights). I'd start with strategy — faster iteration, more interpretable.

4. **How do you want to handle the meta-feedback?** The current environment gives coaching hints ("you haven't explored examples/ yet"). Should we keep this in the top-down version, or remove it to force the agent to develop its own exploration strategy?

5. **SkillClaw integration:** Should the AutoResearch loop also apply to SkillClaw tasks (robotics), or keep it scoped to SuperGeneral (knowledge work) for now?

## References

- [SuperGeneral](https://supergeneral.vercel.app/) — compositional tool environments
- [OpenEnv hackathon](https://github.com/lilyzhng/OpenEnv) — `hackathon/` directory
- [SkillClaw](https://github.com/lilyzhng/SkillClaw) — robotics skill composition
- [Harbor](https://github.com/lilyzhng/harbor) — agent eval framework
- [SkyRL](https://github.com/lilyzhng/SkyRL) — RL training
- [Autoresearch](https://github.com/lilyzhng/autoresearch) — Lily's fork
- [Karpathy's program.md](https://github.com/karpathy/autoresearch/blob/master/program.md)
- [RLM paper](https://arxiv.org/abs/2512.24601) — for future P2 if needed
- [ExCoT-DPO](https://arxiv.org/abs/2503.19988) — execution-based preference data generation
- Builder's design doc: `agents/handoff/specs/design_supergeneral_rlm_reward_20260328.md`
