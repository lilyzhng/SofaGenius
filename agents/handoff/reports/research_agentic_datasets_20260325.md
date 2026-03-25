# Agentic Dataset Discovery Report

**Author:** Genius Researcher | **Date:** 2026-03-25 | **Status:** Complete

## Executive Summary

Surveyed 40+ datasets and frameworks across HuggingFace and GitHub for agentic fine-tuning. The landscape has matured significantly in 2025-2026 — high-quality multi-turn tool-calling data, SWE agent trajectories, and RL training infrastructure are all available with commercial-friendly licenses.

**Key finding:** NVIDIA's Nemotron suite + SWE-smith/SERA provide the most complete foundation for agentic fine-tuning (SFT + RL). Domain-specific agentic data (finance, legal, consulting) remains a major gap — we'd need to synthesize our own.

---

## Tier 1: Core Agentic Datasets (HIGH relevance)

### Multi-Turn Tool-Calling

| Dataset | Size | License | Best For |
|---------|------|---------|----------|
| [nvidia/Nemotron-Agentic-v1](https://huggingface.co/datasets/nvidia/Nemotron-Agentic-v1) | 181K trajectories, 32GB | CC-BY-4.0 | Multi-turn tool-use SFT — anchor dataset |
| [Salesforce/xlam-function-calling-60k](https://huggingface.co/datasets/Salesforce/xlam-function-calling-60k) | 60K | CC-BY-4.0 | Function calling foundation (verified via execution) |
| [Salesforce/APIGen-MT-5k](https://huggingface.co/datasets/Salesforce/APIGen-MT-5k) | 5K | CC-BY-NC-4.0 | Multi-turn agentic (beats GPT-4o on tau-bench) |
| [NousResearch/hermes-function-calling-v1](https://huggingface.co/datasets/NousResearch/hermes-function-calling-v1) | 10-100K | Apache-2.0 | Function calling + structured output + agentic json-mode |
| [lockon/ToolACE](https://huggingface.co/datasets/lockon/ToolACE) | 26,507 APIs | Apache-2.0 | Complex multi-tool composition (ICLR 2025) |

### SWE Agent Trajectories

| Dataset | Size | License | Best For |
|---------|------|---------|----------|
| [SWE-smith](https://huggingface.co/datasets/SWE-bench/SWE-smith) | 50,137 tasks | MIT | Largest SWE training set (40.2% SWE-bench Verified) |
| [nebius/SWE-rebench-openhands](https://huggingface.co/datasets/nebius/SWE-rebench-openhands-trajectories) | 67K trajectories | CC-BY-4.0 | Real GitHub issue resolution across 1,823 repos |
| [nvidia/Nemotron-SWE-v1](https://huggingface.co/datasets/nvidia/Nemotron-SWE-v1) | 59K | CC-BY-4.0 | Code agent SFT via OpenHands framework |
| [SERA](https://github.com/allenai/SERA) | 25K trajectories | Apache-2.0 | 54.2% SWE-bench, 26x cheaper than RL |
| [GAIR/OpenSWE](https://huggingface.co/datasets/GAIR/OpenSWE) | 13K trajectories | Other | Fully transparent SWE training framework |

---

## Tier 2: RL & Preference Data (HIGH for alignment)

| Dataset | Size | License | Best For |
|---------|------|---------|----------|
| [nvidia/Nemotron-RL-Agentic-FC-Pivot-v1](https://huggingface.co/datasets/nvidia/Nemotron-RL-Agentic-Function-Calling-Pivot-v1) | 1-10K | CC-BY-4.0 | RL for tool calling |
| [nvidia/Nemotron-RL-SWE-Pivot-v1](https://huggingface.co/datasets/nvidia/Nemotron-RL-Agentic-SWE-Pivot-v1) | 10-100K | CC-BY-4.0 | RL for SWE agents |
| [trl-lib/prm800k](https://huggingface.co/datasets/trl-lib/prm800k) | 800K step labels | MIT | Process reward modeling (canonical PRM dataset) |
| [openbmb/UltraInteract_pair](https://huggingface.co/datasets/openbmb/UltraInteract_pair) | 286K answers, 219K pairs | MIT | Reasoning preference/DPO with environment interaction |
| [OpenThoughts-Agent](https://github.com/open-thoughts/OpenThoughts-Agent) | 15K SFT + 720 RL | Apache-2.0 | Complete SFT→RL pipeline |
| [DeepSWE/rLLM](https://github.com/agentica-project/rllm) | 4.5K problems | Open source | Full RL recipe (59% SWE-bench Verified SOTA) |

---

## Tier 3: Supplementary & Specialized

| Dataset | Size | License | Best For |
|---------|------|---------|----------|
| [glaiveai/glaive-function-calling-v2](https://huggingface.co/datasets/glaiveai/glaive-function-calling-v2) | 100K-1M | Apache-2.0 | Bulk function calling data mixing |
| [Mustafaege/qwen3.5-toolcalling-v2](https://huggingface.co/datasets/Mustafaege/qwen3.5-toolcalling-v2) | 60K+ | Apache-2.0 | Tool calling + code execution + reasoning chains |
| [Jofthomas/hermes-fc-thinking-V1](https://huggingface.co/datasets/Jofthomas/hermes-function-calling-thinking-V1) | 1-10K | Unspecified | Think-then-act patterns (CoT + tool calling) |
| [smolagents/codeagent-traces](https://huggingface.co/datasets/smolagents/codeagent-traces) | 10-100K | Unspecified | Code-as-action agent traces |
| [argilla/apigen-function-calling](https://huggingface.co/datasets/argilla/apigen-function-calling) | 100K+ | CC-BY-4.0 | Merged function calling (xlam + synthetic) |
| [jdaddyalbs/playwright-mcp-toolcalling](https://huggingface.co/datasets/jdaddyalbs/playwright-mcp-toolcalling) | 1-10K | MIT | Browser agent MCP tool calling |
| [yatin/Creative-Agentic-Tasks-1M](https://huggingface.co/datasets/yatin-superintelligence/Creative-Professionals-Agentic-Tasks-1M) | 1M+ | MIT | Diverse software environments |
| [HuggingFaceH4/ultrafeedback_binarized](https://huggingface.co/datasets/HuggingFaceH4/ultrafeedback_binarized) | 64K prompts | MIT | General DPO alignment |
| [hypervariance/function-calling-sharegpt](https://huggingface.co/datasets/hypervariance/function-calling-sharegpt) | 86,864 | — | Multi-turn function calling in ShareGPT format |

---

## Synthetic Data Generation Tools

| Tool | URL | What It Does |
|------|-----|-------------|
| **NexGAP** | [GitHub](https://github.com/nex-agi/NexGAP) | Generates multi-turn tool-calling trajectories from real MCP tools. Covers 7 tool-call formats. Apache-2.0. |
| **SWE-smith** | [GitHub](https://github.com/SWE-bench/SWE-smith) | Synthesizes SWE tasks from any Python codebase. MIT. |
| **tbench-agentic-pipeline** | [GitHub](https://github.com/Danau5tin/tbench-agentic-data-pipeline) | Multi-agent pipeline using 20+ Claude Code instances for terminal/coding tasks. |
| **ToolsGen** | [GitHub](https://github.com/atasoglu/toolsgen) | Generate tool-calling datasets from JSON tool definitions. MIT. |
| **DataForge** | [GitHub](https://github.com/adoslabsproject-gif/dataforge) | Deterministic SFT + DPO data generation for tool-calling. Apache-2.0. |

---

## RL Training Infrastructure

| Framework | Stars | URL | Key Feature |
|-----------|-------|-----|-------------|
| **verl-agent** | 1,725 | [GitHub](https://github.com/langfengQ/verl-agent) | Multi-turn RL with GiGPO (NeurIPS 2025). Step-wise rewards. |
| **AgentGym-RL** | 647 | [GitHub](https://github.com/WooooDyy/AgentGym-RL) | Long-horizon decision-making via multi-turn RL. MIT. |
| **SWEET-RL** | 265 | [GitHub](https://github.com/facebookresearch/sweet_rl) | Step-wise evaluation for collaborative multi-turn agents. |

---

## Recommended Data Mix for Agentic Fine-Tuning

### Phase 1: SFT (Supervised Fine-Tuning)
- **nvidia/Nemotron-Agentic-v1** (181K) — anchor: multi-turn tool use
- **Salesforce/xlam-function-calling-60k** (60K) — function calling foundation
- **NousResearch/hermes-function-calling-v1** — structured output + agentic json-mode
- **lockon/ToolACE** — complex multi-tool composition
- **SWE-smith** or **nebius/SWE-rebench** — long-horizon code tasks

### Phase 2: RL/DPO (Reinforcement Learning)
- **nvidia/Nemotron-RL-Agentic-FC-Pivot-v1** — RL for tool calling
- **openbmb/UltraInteract_pair** — reasoning preference trees
- **trl-lib/prm800k** — process reward for step-level supervision
- **OpenThoughts-Agent RL** — curated RL tasks with verifiers

### Phase 3: Multi-Turn Refinement
- **Salesforce/APIGen-MT-5k** — verified multi-turn (small but highest quality)
- **Jofthomas/hermes-fc-thinking-V1** — thinking + acting patterns
- **SERA** trajectories — coding agent refinement

---

## Gap Analysis

| Need | Status |
|------|--------|
| Multi-turn tool calling | **Well covered** — Nemotron, APIGen-MT, ToolACE |
| Long-horizon code tasks | **Well covered** — SWE-smith, nebius, Nemotron-SWE, SERA |
| RL with reward signals | **Covered** — Nemotron-RL, prm800k, UltraInteract, OpenThoughts |
| Process reward models | **Emerging** — prm800k (math), ToolPRMBench (2026 paper, data not yet public) |
| Domain-specific (finance, legal) | **GAP** — no agentic datasets exist. Must synthesize using NexGAP/APIGen on domain APIs |
| Composition/decomposition | **Partially covered** — Nemotron-Agentic-v1, ToolACE |
| MCP tool calling | **Emerging** — NexGAP, playwright-mcp-toolcalling |

---

## Curated Lists to Monitor

- [Awesome-Agent-Training](https://github.com/bruno686/Awesome-Agent-Training) — comprehensive index
- [Agentic-RL-Training-Recipes](https://github.com/blacksnail789521/Agentic-RL-Training-Recipes) — RL-focused
- [Computer-Browser-Phone-Use-Agent-Datasets](https://github.com/Khang-9966/Computer-Browser-Phone-Use-Agent-Datasets) — GUI agents

---

## Key Papers (2025-2026)

| Paper | Date | Contribution |
|-------|------|-------------|
| SWE-smith | Apr 2025 | 50K SWE tasks, NeurIPS 2025 Spotlight |
| SERA (SVG) | Jan 2026 | 26x cheaper than RL for coding agents |
| Self-Play SWE-RL | Dec 2025 | Self-play training, no human labels needed |
| GiGPO | 2025 | Fine-grained credit assignment, NeurIPS 2025 |
| APIGen-MT | 2025 | SOTA multi-turn agentic data generation |
| ToolPRMBench | 2026 | Process reward for tool-using agents |
| NexGAP | Dec 2025 | MCP-based agentic data pipeline |
