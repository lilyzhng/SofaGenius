# Agent Benchmarks: Tool Usage, Task Decomposition & Long-Horizon Tasks

**Date:** 2026-03-26
**Researcher:** Genius Researcher
**Focus:** Benchmarks for post-training RE on tool usage and task decomposition

---

## 1. TOOL USAGE BENCHMARKS

### BFCL (Berkeley Function Calling Leaderboard) — V4
- **What:** The de facto standard for evaluating function/tool calling in LLMs
- **Data:** Mix of real-world and curated function signatures; V2 added enterprise/OSS functions
- **Versions:** V1 (AST eval), V2 (enterprise functions), V3 (multi-turn/multi-step), V4 (holistic agentic eval with web search, memory, format sensitivity)
- **Realism:** Moderate-High. Uses real API signatures but tasks are still somewhat constrained
- **Adoption:** Very high — most model providers report BFCL scores
- **Access:** Open-source, PyPI package (`bfcl-eval`), HuggingFace dataset
- **Relevance:** ★★★★★ — Directly tests function calling, tool selection, multi-step tool chaining
- **Links:** [Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html) | [GitHub](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard) | [HF Dataset](https://huggingface.co/datasets/gorilla-llm/Berkeley-Function-Calling-Leaderboard)

### MCP-Bench (Accenture, NeurIPS 2025 Workshop)
- **What:** Benchmarks tool-using agents via Model Context Protocol (MCP) servers
- **Data:** 28 live MCP servers, 250+ tools across finance, travel, scientific computing, academic search
- **Realism:** HIGH — uses real MCP servers with live tool interactions, not mocked APIs
- **Key tests:** Fuzzy tool retrieval (no explicit tool names), multi-hop execution, cross-domain orchestration, intermediate output grounding
- **Adoption:** Newer but growing — accepted at NeurIPS 2025
- **Relevance:** ★★★★★ — Tests exactly what "multi-tool orchestration" means in practice
- **Links:** [Paper](https://arxiv.org/abs/2508.20453) | [GitHub](https://github.com/Accenture/mcp-bench)

### ToolBench / ToolLLM (OpenBMB, ICLR 2024 Spotlight)
- **What:** Open platform for training, serving, and evaluating tool learning
- **Data:** 16,464 real-world RESTful APIs from RapidAPI Hub, 49 categories
- **Evaluation:** ToolEval with Pass Rate and Win Rate metrics
- **Realism:** HIGH — uses real APIs, but some have gone stale over time
- **Variants:** StableToolBench (fixes API staleness), ToolBench-V/R (meta-verification)
- **Adoption:** Very high — ICLR spotlight, widely cited
- **Relevance:** ★★★★☆ — Great for tool selection/chaining but API staleness is a known issue
- **Links:** [GitHub](https://github.com/OpenBMB/ToolBench) | [Leaderboard](https://openbmb.github.io/ToolBench/)

### API-Bank
- **What:** Comprehensive benchmark for tool-augmented LLMs
- **Data:** 73 API tools, 314 tool-use dialogues, 753 API calls; training set: 1,888 dialogues, 2,138 APIs, 1,000 domains
- **Realism:** Moderate — structured but somewhat synthetic dialogues
- **Adoption:** Moderate — well-cited but somewhat dated
- **Relevance:** ★★★☆☆ — Good foundation but superseded by BFCL and ToolBench

### TaskBench (NeurIPS 2024)
- **What:** Framework evaluating 3 critical stages: task decomposition, tool selection, parameter prediction
- **Data:** Uses "Tool Graph" concept with back-instruct generation
- **Realism:** Moderate — synthetic instruction generation
- **Relevance:** ★★★★☆ — Explicitly tests decomposition + tool selection pipeline

---

## 2. TASK DECOMPOSITION & PLANNING BENCHMARKS

### GAIA (Meta, General AI Assistants)
- **What:** 450 questions requiring multi-step reasoning, web browsing, tool use
- **Data:** Real-world questions with unambiguous answers
- **Levels:** L1 (<5 steps), L2 (5-10 steps, multi-tool), L3 (long-term planning, diverse tools)
- **Realism:** HIGH — questions designed to require real tool use and reasoning
- **Top score (2025):** 75% (h2oGPTe Agent) — first "C grade" on the benchmark
- **Adoption:** Very high — Princeton hosts leaderboard, widely reported
- **Relevance:** ★★★★★ — Tests multi-step reasoning + tool integration in realistic scenarios
- **Links:** [Leaderboard](https://hal.cs.princeton.edu/gaia) | [Paper](https://arxiv.org/abs/2311.12983)

### OdysseyBench (2025)
- **What:** Long-horizon workflows across diverse office applications
- **Data:** OdysseyBench+ (300 real-world tasks) + OdysseyBench-Neo (302 synthesized complex tasks)
- **Realism:** HIGH — derived from real-world office use cases
- **Key feature:** Tests long-term contextual dependencies, not just atomic tasks
- **Relevance:** ★★★★☆ — Good for decomposition in professional workflows

### Plan-and-Act (ICML 2025)
- **What:** Framework + evaluation for explicit planning in agent tasks
- **Data:** Synthetic data generation for Planner/Executor split
- **Relevance:** ★★★☆☆ — More of a method paper but defines decomposition evaluation

---

## 3. LONG-HORIZON BENCHMARKS

### Terminal-Bench 2.0 (ICLR 2026)
- **What:** 89 tasks in terminal environments from real professional workflows
- **Data:** Real-world — configuring legacy systems, reimplementing research papers, system administration, security, data science
- **Realism:** VERY HIGH — tasks that professionals are paid to do
- **Top score (2026):** GPT-5.3 Codex at 77.3%
- **No "Pro" variant found** — Terminal-Bench 2.0 IS the harder, real-world version (supersedes v1)
- **Adoption:** High — published at ICLR 2026, multiple organizations compete
- **Related:** Harbor framework for agent evaluation/RL environments
- **Relevance:** ★★★★★ — Long-horizon, real tasks, but terminal/coding focused
- **Links:** [Website](https://www.tbench.ai/) | [GitHub](https://github.com/laude-institute/terminal-bench) | [Paper](https://arxiv.org/abs/2601.11868)

### RE-Bench (METR, ICML 2025)
- **What:** 7 challenging, open-ended ML research engineering environments
- **Data:** Real ML research tasks with human expert comparison (71 attempts by 61 experts, 8hrs each)
- **Realism:** VERY HIGH — actual research engineering tasks
- **Key finding:** Best AI agents score 4x higher than experts at 2hr budget, but experts don't saturate at 8hrs
- **Models tested:** Claude 3.5 Sonnet, o1-preview
- **Adoption:** Moderate-high — ICML 2025, open-sourced environments + transcripts
- **Relevance:** ★★★★★ — Directly tests research engineering capability with human baselines
- **Links:** [METR Blog](https://metr.org/blog/2024-11-22-evaluating-r-d-capabilities-of-llms/) | [Paper](https://arxiv.org/abs/2411.15114)

### SWE-Bench Pro (Scale AI, 2025)
- **What:** 1,865 problems from 41 repos; excludes trivial edits
- **Data:** Real GitHub issues — avg 107.4 lines changed across 4.1 files per problem
- **Realism:** VERY HIGH — real codebases, includes proprietary commercial repos
- **Top score (2026):** ~46% (vs 81% on original SWE-Bench)
- **Adoption:** High — Scale AI leaderboard, widely reported
- **Relevance:** ★★★★☆ — Long-horizon but coding-specific
- **Links:** [Leaderboard](https://labs.scale.com/leaderboard/swe_bench_pro_public) | [Paper](https://arxiv.org/abs/2509.16941)

---

## 4. REAL-WORLD DATA / PROFESSIONAL DOMAIN BENCHMARKS

### APEX-Agents (Mercor)
- **What:** 480 tasks across investment banking, management consulting, and corporate law
- **Data:** Created by actual analysts/consultants/lawyers role-playing 5-10 day client engagements; avg 166 files per world
- **Tools:** Calendar, Chat, Code, Documents, File System, Mail, PDF, Spreadsheets, Presentations + specialized (EDGAR SEC, Fixed Income)
- **Realism:** VERY HIGH — real professional workflows with multi-application orchestration
- **Top score (2026):** 24% (Gemini 3 Flash). Open-source models below 5%
- **Adoption:** Growing — open-sourced benchmark + Archipelago infra
- **Relevance:** ★★★★★ — THE benchmark for professional agentic workflows
- **Links:** [Paper](https://arxiv.org/abs/2601.14242) | [HF Dataset](https://huggingface.co/datasets/mercor/apex-agents) | [Mercor Blog](https://www.mercor.com/blog/introducing-apex-agents/)

### τ-Bench / τ²-Bench (Sierra)
- **What:** Real-world agent benchmark with API tools and user interactions
- **Data:** Real customer service scenarios with tool APIs
- **τ² variant:** Dual-control where both agent and user manipulate shared state
- **Realism:** HIGH — realistic customer service domains
- **Adoption:** High — Claude 3.5 scored well with minimal prompt engineering
- **Relevance:** ★★★★☆ — Good for tool-use in conversational workflows
- **Links:** [GitHub](https://github.com/sierra-research/tau-bench) | [τ²-Bench](https://github.com/sierra-research/tau2-bench)

### OSWorld
- **What:** 369 tasks in real computer environments (Ubuntu, Windows, macOS)
- **Data:** Real web/desktop apps, OS file I/O, cross-application workflows
- **Realism:** VERY HIGH — actual operating system environments
- **Adoption:** High — NeurIPS 2024
- **Relevance:** ★★★★☆ — Real environments but more computer-use than tool-calling
- **Links:** [Website](https://os-world.github.io/) | [Paper](https://arxiv.org/abs/2404.07972)

### WebArena
- **What:** 812 tasks across e-commerce, forums, code repos, CMS
- **Data:** Self-hosted realistic web environments
- **Realism:** HIGH — simulated but realistic web applications
- **Adoption:** Very high — standard web agent benchmark
- **Relevance:** ★★★☆☆ — Web-focused, less about tool orchestration

### FinAgentBench (ACM ICAIF 2025)
- **What:** 26K expert-annotated examples on S&P-500 firms
- **Data:** Real financial data for agentic retrieval
- **Relevance:** ★★★★☆ — Domain-specific finance benchmark

### FAB (Finance Agent Benchmark)
- **What:** 537 expert-authored research questions across 9 categories
- **Data:** Real financial data from simple retrieval to financial modeling
- **Relevance:** ★★★★☆ — Professional finance domain

---

## 5. ANTHROPIC / OPENAI / GOOGLE INTERNAL EVALUATIONS

### Anthropic
- **SHADE-Arena:** 17 complex agentic tasks testing sabotage detection — more safety-focused than capability-focused. Top sabotage rate: 27% (Claude 3.7 Sonnet). Not publicly released to avoid contamination.
- **Bloom:** Open-source agentic framework for automated behavioral evaluations
- **Tool Search / Programmatic Tool Calling:** Anthropic has built internal evaluation for these Claude-specific capabilities but benchmarks are not public
- **Joint eval with OpenAI (2025):** Cross-tested alignment evaluations on each other's models

### OpenAI
- **Internal evals framework (openai/evals):** 18K+ stars, open-source eval framework. Used for internal function-calling and tool-use evaluation
- **SWE-Bench / Terminal-Bench results:** OpenAI actively benchmarks Codex models on these

### Google
- **No specific public tool-use benchmark identified** — Google relies on third-party benchmarks (BFCL, GAIA, etc.) for reporting

---

## 6. SUMMARY: TOP BENCHMARKS BY RELEVANCE TO "POST-TRAINING RE FOR TOOL USAGE & TASK DECOMPOSITION"

| Rank | Benchmark | Why It Matters | Real Data? | Adoption |
|------|-----------|---------------|------------|----------|
| 1 | **BFCL V4** | Direct function calling eval, multi-step, agentic | Mix | Very High |
| 2 | **MCP-Bench** | Live multi-tool orchestration via MCP | Yes | Growing |
| 3 | **APEX-Agents** | Professional workflows (IB/consulting/law) | Yes | Growing |
| 4 | **GAIA** | Multi-step reasoning + tool integration | Yes | Very High |
| 5 | **RE-Bench** | Research engineering with human baselines | Yes | High |
| 6 | **Terminal-Bench 2.0** | Long-horizon real terminal tasks | Yes | High |
| 7 | **ToolBench** | 16K+ real APIs, tool selection/chaining | Yes | Very High |
| 8 | **τ-Bench/τ²** | Tool use in conversational workflows | Yes | High |
| 9 | **TaskBench** | Explicit decomposition + tool selection eval | Synthetic | Moderate |
| 10 | **SWE-Bench Pro** | Long-horizon coding with real repos | Yes | High |

---

## 7. KEY TAKEAWAYS

1. **BFCL V4 is the industry standard** for function calling — anyone working on tool-use post-training should know it deeply
2. **MCP-Bench is the emerging standard** for 2025-2026 — aligns with MCP protocol adoption
3. **APEX-Agents is uniquely valuable** — only benchmark testing professional knowledge work (IB, consulting, law) with multi-app orchestration; top agents at only 24%
4. **No Terminal-Bench "Pro" exists** — Terminal-Bench 2.0 IS the harder variant
5. **RE-Bench is the gold standard** for comparing AI vs human on research engineering
6. **Biggest gap in current benchmarks:** Most still focus on coding/web tasks. Professional domain tool-use (finance, legal, consulting) is underserved — APEX-Agents is the main exception
7. **For career narrative:** Demonstrating expertise across BFCL, MCP-Bench, APEX-Agents, and RE-Bench positions you at the intersection of tool-use capability and real-world professional workflows
