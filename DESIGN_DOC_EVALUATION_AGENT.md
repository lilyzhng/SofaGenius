# Design Doc: Evaluation Agent for SofaGenius

## 1. Problem Statement

Evaluation in SofaGenius is currently limited in three ways:

1. **Domain-locked**: The existing eval pipeline (`modal_app/eval.py`) is hardcoded to HTML/CSS UI code generation — it uses Playwright screenshots and a Tailwind CSS scoring rubric. It cannot evaluate models trained on different tasks.

2. **Bundled with Launch**: The eval tools (`propose_eval`, `launch_eval`) live inside the Launch agent, mixed with fine-tuning tools. The existing `propose_eval` also has a bug (`modal_launcher.py:366` references `cost['estimated_hours']` but the function returns `estimated_seconds`), confirming it has never been used end-to-end.

3. **No agent evaluation**: Standard model benchmarks (MMLU, HumanEval) test isolated capabilities, but the real need is evaluating **agents** — long traces of user-LLM interaction with tool use, multi-step planning, and task completion in realistic environments. This is fundamentally different from model evaluation.

### The Vision

The future is personalized agents — coding agents, design agents, research agents. Evaluating these requires testing the **full agent system** (prompt + tools + memory + reasoning) on realistic, long-horizon tasks, not just the underlying model on synthetic benchmarks. SofaGenius should be able to evaluate:

1. **Any LLM agent** on coding, tool-use, and multi-step tasks
2. **SofaGenius itself** — its own subagents on real ML research workflows
3. **Any HuggingFace model** on standard benchmarks (as a secondary capability)

---

## 2. Goals

- **Agent-evaluation-first** architecture using Inspect AI as the core framework
- **Three evaluation tiers**: Agent eval (primary), model benchmarks (secondary), custom visual eval (domain-specific)
- **Works standalone**: Evaluate any agent/model, not just SofaGenius-trained ones
- **Post-training integration**: Pick up trained models from session context
- **New EvalResultsCard**: Dedicated frontend card for results
- **Separate Modal app**: Independent `sofa-genius-eval` for all eval workloads

---

## 3. Why Inspect AI

[Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) (UK AI Security Institute) is the most complete agent evaluation framework available:

| Feature | Inspect AI | lm-eval-harness | lighteval |
|---------|-----------|-----------------|-----------|
| **Agent evaluation** | Native — multi-turn traces, tool use, sandboxed environments | No | No |
| **Pre-built agent evals** | 100+ including SWE-bench, GAIA, AgentBench, WebArena | 200+ model benchmarks | 1000+ model benchmarks |
| **Sandboxing** | Docker, Kubernetes, **Modal**, Proxmox | No | No |
| **External agent support** | Run Claude Code, Codex CLI, Gemini CLI, custom agents | No | No |
| **MCP tool support** | Yes | No | No |
| **Tool calling** | Built-in bash, python, web browse, text edit, web search | No | No |
| **LLM-as-judge scoring** | Native | In progress | Native |
| **Standard model benchmarks** | Yes (MMLU, HumanEval, etc.) | Yes (primary focus) | Yes (primary focus) |
| **Trace recording & visualization** | Built-in Inspect View | No | No |

Inspect AI covers all three tiers:
- **Agent eval**: SWE-bench, GAIA, custom agent tasks with sandboxed execution
- **Model benchmarks**: MMLU, HumanEval, GSM8K, ARC (via its built-in eval suite)
- **Custom eval**: Define custom tasks with LLM-as-judge or VLM-as-judge scoring

We use Inspect AI as the **primary** framework, with lm-eval-harness and lighteval available as backends for users who want maximum benchmark coverage or HF Hub integration.

---

## 4. Architecture

### 4.1 New Files

```
backend/
├── agents/
│   └── evaluation.py              # NEW — Evaluation subagent (7 tools)
├── tools/
│   └── eval_tools.py              # NEW — Evaluation tool implementations
├── modal_app/
│   ├── app.py                     # MODIFIED — remove eval function
│   ├── eval_app.py                # NEW — Separate Modal app for all evaluations
│   ├── eval.py                    # EXISTING — keep for visual render eval
│   ├── inspect_runner.py          # NEW — Inspect AI agent eval runner
│   ├── benchmark_eval.py          # NEW — lm-eval-harness / lighteval runner
│   └── lighteval_runner.py        # NEW — lighteval benchmark runner

frontend/src/
├── types.ts                       # MODIFIED — add EvalResultsCard type
├── components/
│   ├── CardsPanel.tsx              # MODIFIED — add EvalResultsCard routing
│   └── EvalResultsCard.tsx         # NEW — Evaluation results card component
```

### 4.2 Orchestrator Changes

**File**: `backend/orchestrator.py`

```python
# Add to routing categories:
- evaluation: evaluating models or agents, benchmarks, MMLU, HumanEval,
  SWE-bench, agent testing, model quality, eval results, comparing scores,
  running evaluations, coding agent evaluation

# Agent map:
_AGENT_MAP["evaluation"] = evaluation
```

### 4.3 Migration from Launch Agent

Fully migrate eval out of Launch agent:
- Remove `propose_eval`, `launch_eval` from `agents/launch.py`
- Remove eval imports and `_estimate_eval_cost` from `tools/modal_launcher.py`
- Launch agent keeps only 3 tools: `propose_finetune`, `modify_and_propose`, `launch_finetune`

---

## 5. Evaluation Agent Design

### 5.1 System Prompt

The agent is an evaluation specialist that:
- Recommends the right evaluation approach based on what the user wants to evaluate
- Can evaluate agents (coding agents, tool-use agents, SofaGenius subagents) on realistic tasks
- Can evaluate models on standard benchmarks
- Can run custom visual evaluations with VLM-as-judge
- Uses session context to pick up recently trained models
- Follows propose -> approve -> launch workflow

### 5.2 Tools (7 tools)

| Tool | Purpose | Card Output |
|------|---------|-------------|
| `list_evaluations` | List available evaluation suites: agent evals (SWE-bench, GAIA), model benchmarks (MMLU, HumanEval), and custom evals | None (text) |
| `propose_agent_eval` | Propose an agent evaluation — SWE-bench, GAIA, or custom agent task suite | `eval_results_card` (status=proposed) |
| `propose_benchmark_eval` | Propose standard model benchmarks via lm-eval-harness or lighteval | `eval_results_card` (status=proposed) |
| `propose_custom_eval` | Propose custom eval (visual render + VLM judge, or user-defined) | `eval_results_card` (status=proposed) |
| `modify_eval_config` | Tweak any eval config (change tasks, limits, model, framework, etc.) | `eval_results_card` (status=proposed) |
| `launch_eval` | Launch the approved eval job on Modal | `eval_results_card` (status=running) |
| `get_eval_results` | Fetch completed eval results from W&B / Inspect logs | `eval_results_card` (status=completed) |

### 5.3 Three-Tier Evaluation System

#### Tier 1: Agent Evaluation (Primary — via Inspect AI)

Evaluates the **full agent system** on realistic multi-step tasks.

**Available agent eval suites:**

| Suite | What it tests | Tasks | Environment |
|-------|--------------|-------|-------------|
| SWE-bench Verified | Coding agent on real GitHub issues | 500 | Docker sandbox with real repos |
| PostTrainBench | Post-training agent capability (fine-tune a base LLM to maximize benchmark score) | 28+ (4 models × 7 benchmarks) | H100 GPU sandbox |
| GAIA | General AI assistant with tool use | 466 | Web browser, file system, APIs |
| MCPEval | MCP-based agent evaluation across real-world domains | Multi-domain | MCP servers |
| Custom SofaGenius | SofaGenius subagent quality | User-defined | SofaGenius API |

**Agent Harness Evaluation** — A critical capability. The same model (e.g., Opus 4.6) can produce very different outcomes depending on the agent harness (Claude Code vs Cursor vs custom). We evaluate harness quality across six dimensions:

| Dimension | What it measures | How to test |
|-----------|-----------------|-------------|
| Task completion | Does it solve the problem? | Same tasks, measure pass rate |
| Efficiency | How many tokens/steps/tool calls? | Compare trace lengths for identical tasks |
| Error recovery | Does it recover from failures? | Inject failures, measure recovery rate |
| Context management | Does it degrade in long sessions? | Progressively longer tasks |
| Tool selection | Does it pick the right tool? | Multi-tool tasks, selection accuracy |
| Scaffolding quality | Prompt design, memory, planning | A/B test different harnesses on same model |

The evaluation approach: **Run the same model through different agent harnesses on identical task suites, comparing trace quality + outcomes.** This isolates the harness contribution from the model contribution. PostTrainBench is particularly relevant here — it tests whether an agent can effectively conduct post-training (exactly what SofaGenius does).

**`propose_agent_eval` parameters:**
- `agent_type`: What agent to evaluate — `"model"` (evaluate an LLM's agent capability), `"external"` (test a running agent endpoint), or `"sofagenius"` (self-eval)
- `model_name`: For model-based agents, the HF model to test
- `eval_suite`: Which evaluation suite (e.g., `"swe_bench_verified"`, `"gaia"`, `"custom"`)
- `limit`: Max tasks (for quick eval)
- `sandbox`: `"docker"` (default) or `"modal"` — where to run agent tasks
- `gpu_type`: GPU for model inference

**How it works:**
1. Inspect AI loads the evaluation suite (e.g., SWE-bench)
2. For each task, it sets up a sandboxed environment (Docker/Modal)
3. It runs the agent (sends messages, provides tools, records trace)
4. It scores the output (tests passing, task completion, LLM-as-judge)
5. Results are logged to W&B and returned as an EvalResultsCard

#### Tier 2: Model Benchmarks (Secondary — via lm-eval-harness / lighteval)

Evaluates the **model in isolation** on standard academic benchmarks.

| Framework | Best for | Speed |
|-----------|----------|-------|
| lm-eval-harness | Classic benchmarks (MMLU, HumanEval), publishable scores | Good |
| lighteval | HF Hub integration, community benchmarks, vLLM speed | Fast |

The agent decides which framework to recommend:
- **lm-eval-harness**: User asks for specific benchmarks by name, wants comparable results
- **lighteval**: User wants HF Hub push, newer benchmarks, faster eval via vLLM

**`propose_benchmark_eval` parameters:**
- `model_name`: Any HF model path
- `benchmarks`: JSON array of benchmark names
- `framework`: `"lm_eval_harness"` (default) or `"lighteval"`
- `backend`: `"hf"` (default), `"vllm"`, or `"sglang"` — inference engine
- `num_fewshot`, `limit`, `gpu_type`

#### Tier 3: Custom Visual Evaluation (Domain-specific)

Evaluates models that produce **visual output** requiring rendering and VLM-as-judge scoring.

This is the only tier that uses Playwright to render HTML and take screenshots. Neither Inspect AI, lm-eval-harness, nor lighteval support visual rendering pipelines.

The existing `eval.py` is refactored to:
- Accept a configurable rubric (not hardcoded to Tailwind CSS)
- Support any code-generation model (not just UI models)
- Keep the Playwright + VLM judge pipeline as the unique value-add

### 5.4 Framework Decision Guide (in system prompt)

```
User says "evaluate my coding agent on real tasks"
  → Tier 1: Agent eval (Inspect AI + SWE-bench)

User says "how does my model score on MMLU?"
  → Tier 2: Model benchmark (lm-eval-harness)

User says "compare my model's UI output quality"
  → Tier 3: Custom visual eval (Playwright + VLM judge)

User says "evaluate my model on standard benchmarks and push to HF"
  → Tier 2: Model benchmark (lighteval, with HF push)

User says "test if my fine-tuned model is better at coding"
  → Tier 1 if testing agent capability (SWE-bench)
  → Tier 2 if testing code generation (HumanEval, MBPP)
```

---

## 6. Modal App: `sofa-genius-eval`

### 6.1 Separate App Rationale

Different eval tiers have very different dependencies. Keeping them in a separate Modal app with per-function images means clean separation, independent deployment, and no dependency conflicts.

### 6.2 Modal Functions & Images

```python
app = modal.App("sofa-genius-eval")

# --- Image for Inspect AI agent evaluations ---
inspect_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "inspect-ai",         # Core framework
        "inspect-evals",      # Pre-built evals (SWE-bench, GAIA, etc.)
        "wandb",
        "hf-transfer",
    )
    .env({"HF_HOME": "/model_cache"})
)

# --- Image for lm-eval-harness benchmarks ---
lm_eval_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "lm-eval[all]",
        "accelerate",
        "wandb",
        "hf-transfer",
    )
    .env({"HF_HOME": "/model_cache"})
)

# --- Image for lighteval benchmarks ---
lighteval_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "lighteval[accelerate,extended_tasks]",
        "wandb",
        "hf-transfer",
    )
    .env({"HF_HOME": "/model_cache"})
)

# --- Image for custom visual eval (Playwright + VLM judge) ---
custom_eval_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "unsloth[cu128-torch270]",
        "datasets", "hf-transfer", "wandb",
        "openai", "playwright",
    )
    .run_commands("playwright install --with-deps chromium")
    .env({"HF_HOME": "/model_cache"})
)

@app.function(image=inspect_image, gpu="A100-80GB", ...)
def run_agent_eval(config_dict: dict) -> dict:
    """Run agent evaluation via Inspect AI."""
    from backend.modal_app.inspect_runner import agent_eval_impl
    return agent_eval_impl(config_dict)

@app.function(image=lm_eval_image, gpu="A100-80GB", ...)
def run_lm_eval(config_dict: dict) -> dict:
    """Run standard benchmarks via lm-eval-harness."""
    from backend.modal_app.benchmark_eval import lm_eval_impl
    return lm_eval_impl(config_dict)

@app.function(image=lighteval_image, gpu="A100-80GB", ...)
def run_lighteval(config_dict: dict) -> dict:
    """Run benchmarks via HuggingFace lighteval."""
    from backend.modal_app.lighteval_runner import lighteval_impl
    return lighteval_impl(config_dict)

@app.function(image=custom_eval_image, gpu="A100-80GB", ...)
def run_custom_eval(config_dict: dict) -> dict:
    """Run visual rendering eval (Playwright + VLM judge)."""
    from backend.modal_app.eval import eval_impl
    return eval_impl(config_dict)
```

### 6.3 Model Serving & Inference Backend

All evaluation runs on **Modal's serverless GPUs** — model loaded on-demand, evaluated, container shuts down. No persistent serving.

**Inference backends by eval tier:**

| Eval Tier | Inference Backend | Notes |
|-----------|------------------|-------|
| Agent eval (Inspect AI) | Configurable — HF transformers, vLLM, or API-based | Inspect supports both local models and API endpoints |
| lm-eval-harness | `hf`, `vllm`, or `sglang` | All three natively supported |
| lighteval | `accelerate`, `vllm`, or `nanotron` | vLLM fastest for generative tasks |
| Custom visual eval | Unsloth `FastLanguageModel` | Fast 4-bit inference for rendering tasks |

The agent recommends `vllm` for generative tasks and `hf`/`accelerate` for classification tasks.

**Why not Unsloth for benchmarks?** Unsloth is a training optimization library with a fast model loader. It's useful for single-sample inference (used in custom eval), but provides no benchmark infrastructure, no batching optimization, and no evaluation task management. vLLM/SGLang handle high-throughput inference for benchmarks.

---

## 7. Inspect AI Agent Eval Implementation (`inspect_runner.py`)

```python
def agent_eval_impl(config_dict: dict) -> dict:
    """Run agent evaluation via Inspect AI."""
    import inspect_ai
    from inspect_ai import eval as inspect_eval
    from inspect_ai.log import read_eval_log
    import wandb

    model_name = config_dict["model_name"]
    eval_suite = config_dict["eval_suite"]  # "swe_bench_verified", "gaia", etc.
    limit = config_dict.get("limit", None)
    wandb_project = config_dict.get("wandb_project", "sofa-genius-eval")

    run_name = f"agent-{model_name.split('/')[-1]}-{eval_suite}"
    wandb.init(project=wandb_project, name=run_name, config=config_dict)

    # Map eval suite to Inspect task
    SUITE_MAP = {
        "swe_bench_verified": "inspect_evals/swe_bench",
        "gaia": "inspect_evals/gaia",
        "gpqa": "inspect_evals/gpqa",
        "humaneval": "inspect_evals/humaneval",
        "mbpp": "inspect_evals/mbpp",
        # PostTrainBench: custom Inspect task wrapping the PostTrainBench framework
        "posttrain_bench": "backend.evals.posttrain_bench",
    }

    task = SUITE_MAP.get(eval_suite, eval_suite)

    # Run evaluation
    logs = inspect_eval(
        task,
        model=f"hf/{model_name}",
        limit=limit,
        log_dir="/results/inspect_logs",
    )

    # Parse results from Inspect logs
    log = read_eval_log(logs[0])
    results = log.results

    task_results = {}
    for metric_name, metric_value in results.metrics.items():
        task_results[metric_name] = {
            "score": round(metric_value.value * 100, 2),
            "metric": metric_value.name,
        }
        wandb.log({f"{metric_name}": metric_value.value})

    # Per-sample results
    sample_results = []
    for sample in log.samples:
        sample_results.append({
            "id": sample.id,
            "score": sample.score.value if sample.score else 0,
            "turns": len(sample.messages),
            "tool_calls": sum(1 for m in sample.messages if m.role == "tool"),
        })

    avg_score = results.metrics.get("accuracy", results.metrics.get("mean_score"))
    avg_value = round(avg_score.value * 100, 2) if avg_score else 0

    wandb.summary["avg_score"] = avg_value
    wandb.summary["total_tasks"] = len(log.samples)
    wandb.summary["eval_suite"] = eval_suite
    wandb_url = wandb.run.url
    wandb.finish()

    return {
        "model_name": model_name,
        "eval_suite": eval_suite,
        "eval_type": "agent",
        "task_results": task_results,
        "sample_results": sample_results[:50],  # cap for card size
        "avg_score": avg_value,
        "total_tasks": len(log.samples),
        "wandb_url": wandb_url,
        "run_name": run_name,
    }
```

---

## 8. Frontend: EvalResultsCard

### 8.1 TypeScript Type

```typescript
export type EvalStatus = "proposed" | "launching" | "running" | "completed" | "failed";
export type EvalTier = "agent" | "benchmark" | "custom";

export interface TaskScore {
  task: string;
  score: number;
  stderr?: number;
  metric: string;
}

export interface AgentSampleResult {
  id: string;
  score: number;
  turns: number;
  tool_calls: number;
}

export interface CustomEvalScore {
  base_avg_score?: number;
  lora_avg_score?: number;
  score_improvement?: number;
  num_samples: number;
}

export interface EvalResultsCard {
  card_type: "eval_results_card";
  title: string;
  eval_tier: EvalTier;
  status: EvalStatus;
  model_name: string;
  config: Record<string, unknown>;
  cost_estimate?: CostEstimate;
  summary: string;

  // Agent eval results (eval_tier === "agent")
  eval_suite?: string;
  task_scores?: TaskScore[];
  sample_results?: AgentSampleResult[];
  total_tasks?: number;

  // Benchmark results (eval_tier === "benchmark")
  benchmark_scores?: TaskScore[];
  framework?: string;  // "lm_eval_harness" | "lighteval"

  // Custom eval results (eval_tier === "custom")
  custom_scores?: CustomEvalScore;

  // Shared
  avg_score?: number;
  modal_function_call_id?: string;
  wandb_url?: string;
  requires_approval: boolean;
}
```

### 8.2 Card Component Design

**Proposed state**: Config summary, cost estimate, "Approve & Launch" button.

**Running state**: Progress indicator, elapsed time, polls `/api/launch/status/{id}`.

**Completed state** (varies by tier):

- **Agent eval**: Task completion rate, per-task pass/fail breakdown, agent trace stats (avg turns, tool calls per task), score distribution chart.
- **Benchmark**: Horizontal bar chart of per-benchmark scores, color-coded by range (green >80%, yellow 60-80%, red <60%), framework badge (lm-eval/lighteval).
- **Custom visual**: Base vs fine-tuned score comparison with delta, per-sample timeline.
- **All tiers**: Average score badge, W&B link for full details.

### 8.3 Card Routing

Add to `CardsPanel.tsx`:
```tsx
import EvalResultsCard from "./EvalResultsCard";

// In CARD_META:
eval_results_card: { label: "Eval", icon: <ClipboardCheck size={12} /> },

// In render:
{card.card_type === "eval_results_card" && (
  <EvalResultsCard card={card} onWandbUrl={onWandbUrl} />
)}
```

---

## 9. Session Context Integration

The eval agent reads session context from the orchestrator:

```python
# In orchestrator.py:
if category == "evaluation":
    system_prompt += _build_wandb_context(wandb_api_key)
    system_prompt += _build_launch_context(wandb_api_key, session_id)
    system_prompt += _build_hf_context(hf_token)
```

After a training run, when the user says "evaluate my model" or "how did it do?":
- The agent knows the trained model (HF repo) from session context
- It can recommend the appropriate evaluation tier
- For a fine-tuned code model → suggest SWE-bench agent eval + HumanEval benchmark
- For a general model → suggest MMLU + standard benchmarks

---

## 10. Cost Estimation

### Agent Eval (Inspect AI)
```python
AGENT_EVAL_SIZES = {
    "swe_bench_verified": {"tasks": 500, "sec_per_task": 120},
    "posttrain_bench": {"tasks": 28, "sec_per_task": 36000},  # 10hr per task
    "gaia": {"tasks": 466, "sec_per_task": 60},
    "gpqa": {"tasks": 448, "sec_per_task": 10},
}
```

### Model Benchmarks
```python
BENCHMARK_SIZES = {
    "mmlu": 14042, "hellaswag": 10042, "arc_easy": 2376,
    "arc_challenge": 1172, "humaneval": 164, "gsm8k": 1319,
}
# ~2 seconds per sample for 7B-14B models on A100
```

### Custom Visual Eval
```python
# ~120 sec/sample with judge, ~60 sec/sample without
```

---

## 11. Implementation Plan

### Phase 1: Backend Agent + Tools
1. Create `backend/tools/eval_tools.py` — all 7 tool implementations
2. Create `backend/agents/evaluation.py` — system prompt, tool schemas, dispatch
3. Update `orchestrator.py` — add `evaluation` routing and context injection
4. Remove eval from Launch agent, fix `estimated_hours` bug
5. Update `agents/base.py` — add `_summarize_tool_result` entries for new tools

### Phase 2: Modal Eval App
1. Create `backend/modal_app/eval_app.py` — `sofa-genius-eval` app with 4 functions
2. Create `backend/modal_app/inspect_runner.py` — Inspect AI agent eval
3. Create `backend/modal_app/benchmark_eval.py` — lm-eval-harness runner
4. Create `backend/modal_app/lighteval_runner.py` — lighteval runner
5. Refactor existing `eval.py` — configurable rubric, not hardcoded to Tailwind

### Phase 3: Frontend
1. Add EvalResultsCard types to `frontend/src/types.ts`
2. Create `frontend/src/components/EvalResultsCard.tsx`
3. Update `CardsPanel.tsx` to route `eval_results_card`
4. Add Pydantic models to `backend/models.py`

### Phase 4: Testing & Integration
1. Verify orchestrator routes eval queries correctly
2. Test propose -> approve -> launch workflow
3. Verify EvalResultsCard renders for all three tiers

---

## 12. Updated Architecture

```
                            User message
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        Orchestrator (Haiku)                         │
│                                                                      │
│   Routes to 5 subagents:                                            │
│   training | data | scout | launch | evaluation (NEW)               │
└─────┬──────────┬──────────┬──────────┬──────────┬───────────────────┘
      │          │          │          │          │
      ▼          ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ Training │ │   Data   │ │  Scout   │ │  Launch  │ │  Evaluation  │
│  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │ │    Agent     │
│  4 tools │ │  8 tools │ │  4 tools │ │  3 tools │ │   7 tools    │
│          │ │          │ │          │ │          │ │              │
│ W&B mon. │ │ SQL/Duck │ │ HF scout │ │ Propose  │ │ Agent eval   │
│ Anomaly  │ │ Stats    │ │ Personal │ │ Modify   │ │ Benchmarks   │
│ Compare  │ │ Plots    │ │ + public │ │ Launch   │ │ Custom eval  │
│ Health   │ │ Convert  │ │ Draft    │ │ (FT only)│ │ Results      │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘
     │            │            │            │               │
     ▼            ▼            ▼            ▼               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        External Services                             │
│                                                                      │
│   Anthropic API ─── Claude Sonnet (subagents) + Haiku (routing)      │
│   W&B API ───────── Training metrics + eval results                  │
│   HuggingFace ───── Models, datasets                                 │
│   Modal ─────────── sofa-genius-launcher (fine-tuning)               │
│                      sofa-genius-eval (NEW):                         │
│                        ├── run_agent_eval (Inspect AI)               │
│                        ├── run_lm_eval (lm-eval-harness)            │
│                        ├── run_lighteval (lighteval)                 │
│                        └── run_custom_eval (Playwright + VLM)        │
│   Twitter/X ─────── Post drafts                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 13. Decisions Made

| Question | Decision |
|----------|----------|
| Branch | Develop on `claude/add-evaluation-agent-pSZ4G` |
| Primary framework | Inspect AI for agent evaluation |
| Secondary frameworks | lm-eval-harness + lighteval for model benchmarks |
| Custom eval | Keep Playwright + VLM judge for visual render eval |
| Inference backends | vLLM, SGLang, HF transformers (configurable per eval) |
| Modal setup | Separate `sofa-genius-eval` app with 4 functions |
| Migration | Fully migrate eval out of Launch agent |
| Card type | New `EvalResultsCard` with three visual modes |
| Scope | Agent-eval-first: SWE-bench, GAIA, coding agents, self-eval |
| Model serving | Serverless on Modal — no persistent serving |

---

## 14. References

### Agent Evaluation Frameworks
- [Inspect AI — GitHub](https://github.com/UKGovernmentBEIS/inspect_ai) — Core agent evaluation framework
- [Inspect AI — Documentation](https://inspect.aisi.org.uk/)
- [Inspect Evals — Pre-built evaluations](https://inspect.aisi.org.uk/evals/)
- [Inspect Sandboxing Toolkit](https://www.aisi.gov.uk/blog/the-inspect-sandboxing-toolkit-scalable-and-secure-ai-agent-evaluations)

### Agent Benchmarks
- [PostTrainBench](https://posttrainbench.com/) ([GitHub](https://github.com/aisa-group/PostTrainBench)) — Post-training agent evaluation
- [SWE-bench — Overview](https://www.swebench.com/SWE-bench/)
- [SWE-bench Pro — Leaderboard](https://scale.com/leaderboard/swe_bench_pro_public)
- [MCPEval — MCP-based agent evaluation](https://arxiv.org/abs/2507.12806)
- [mcp-agent — Agent framework with eval support](https://github.com/lastmile-ai/mcp-agent)

### Agent Harness Design
- [Anthropic — Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Anthropic — Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
- [Agent Harness Principles (Vanishing Gradients)](https://hugobowne.substack.com/p/ai-agent-harness-3-principles-for)

### Model Evaluation Frameworks
- [lm-eval-harness — GitHub](https://github.com/EleutherAI/lm-evaluation-harness)
- [lighteval — GitHub](https://github.com/huggingface/lighteval)
- [lighteval — Documentation](https://huggingface.co/docs/lighteval/main/en/index)
- [HuggingFace Evaluation Guidebook](https://huggingface.co/spaces/OpenEvals/evaluation-guidebook)
