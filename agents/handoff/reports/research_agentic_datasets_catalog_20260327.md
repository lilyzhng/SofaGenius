# Agentic Dataset Catalog — For Data + Eval Agent Training

**Date:** 2026-03-27
**Author:** Genius Researcher
**Purpose:** Comprehensive catalog of datasets and training infrastructure relevant to building our Data + Eval Agent

---

## Executive Summary

The agentic training data landscape has matured dramatically in late 2025 / early 2026. We found **20+ relevant datasets** across tool-calling, text-to-SQL, code agents, and RL training. Three standout finds change our product strategy:

1. **DataMind-12K** — Literally data analysis agent trajectories. ICLR 2026. Their 14B model beats GPT-5 on data analysis benchmarks.
2. **Snowflake AWM-1K** — SQL-backed tool-use environments with MCP interface and verification. Almost a template for our agent.
3. **BIRD-Interact** — SQL agent trajectories with execution feedback. ICLR 2026 Oral. Best LLMs only achieve 16.33% success.

Plus a critical methodology: **ExCoT-DPO** (Snowflake, ACL 2025) shows how to generate preference training data purely from SQL execution feedback — no human annotations needed.

---

## Tier 1: Must-Have — Directly Maps to Data + Eval Agent

### 1. DataMind-12K ⭐
| Field | Detail |
|-------|--------|
| **Source** | [github.com/zjunlp/DataMind](https://github.com/zjunlp/DataMind) |
| **Size** | 12K high-quality trajectories |
| **Format** | Multi-turn agent trajectories |
| **License** | Academic release (ICLR 2026) |
| **Contains** | Data analysis agent trajectories spanning diverse domains, task categories, and file formats. Recursive easy-to-hard task composition. SFT + RL training recipe. |
| **Key result** | DataMind-14B achieves SOTA 71.16%, beating GPT-5 and DeepSeek-V3.1 on data analysis benchmarks |
| **Relevance** | **EXTREMELY HIGH** — closest existing work to what we're building. Study their trajectory format, task taxonomy, and training recipe. |

### 2. Snowflake AWM-1K ⭐
| Field | Detail |
|-------|--------|
| **Source** | [HF: Snowflake/AgentWorldModel-1K](https://huggingface.co/datasets/Snowflake/AgentWorldModel-1K) / [GitHub](https://github.com/Snowflake-Labs/agent-world-model) |
| **Size** | 1,000 environments, 35K tools, 10K tasks with verification code |
| **Format** | Code-driven SQL database-backed environments via MCP interface |
| **License** | Open source |
| **Contains** | Fully synthetic multi-turn tool-use environments: finance, travel, retail, healthcare, education, IoT. Each has databases, tools, and verifiable outcomes. |
| **Relevance** | **EXTREMELY HIGH** — SQL-backed, MCP-native, tool-use, multi-turn, with verification. Almost a direct template for our data agent. |

### 3. BIRD-Interact ⭐
| Field | Detail |
|-------|--------|
| **Source** | [github.com/bird-bench/BIRD-Interact](https://github.com/bird-bench/BIRD-Interact) / [HF: birdsql/bird-interact-full](https://huggingface.co/datasets/birdsql/bird-interact-full) |
| **Size** | 600 annotated tasks (300 lite, 600 full) |
| **Format** | Multi-turn with execution feedback |
| **License** | Open (ICLR 2026 Oral) |
| **Contains** | Two modes: conversational interaction (c-Interact) and agentic interaction (a-Interact). Multi-turn SQL agent trajectories with execution feedback. |
| **Key result** | Best LLMs only achieve 16.33% success rate — lots of room for improvement |
| **Relevance** | **VERY HIGH** — exactly SQL agent trajectories, not just QA pairs. Low solve rate = valuable training signal. |

### 4. TOUCAN-1.5M
| Field | Detail |
|-------|--------|
| **Source** | [github.com/TheAgentArk/Toucan](https://github.com/TheAgentArk/Toucan) / [HF: Agent-Ark/Toucan-1.5M](https://huggingface.co/datasets/Agent-Ark/Toucan-1.5M) |
| **Size** | 1.53M trajectories from 495 real-world MCP servers, 2,000+ tools |
| **Format** | Multi-round, multi-turn tool-calling trajectories |
| **License** | Apache 2.0 |
| **Contains** | Sequential and parallel tool calls with real tool execution. 3 teacher models, 5 query-generation models. |
| **Relevance** | **HIGH** — massive scale, MCP-native, Apache licensed. Good for tool-calling capability warmup. |

### 5. SQaLe Text-to-SQL (517K)
| Field | Detail |
|-------|--------|
| **Source** | [HF: trl-lab/SQaLe-text-to-SQL-dataset](https://huggingface.co/datasets/trl-lab/SQaLe-text-to-SQL-dataset) |
| **Size** | 517,676 triples from 135,875 schemas |
| **Format** | HF datasets (schema, question, SQL query, metadata) |
| **License** | TBD |
| **Contains** | Execution-validated SQL. Realistic schema diversity, complex query structures, linguistically varied NL questions. |
| **Relevance** | **HIGH** — massive scale, execution-validated, grounded in real schemas. Good for text-to-SQL foundation. |

---

## Tier 2: High Value — Training Methodology + RL Signals

### 6. ExCoT-DPO Method (Snowflake, ACL 2025)
| Field | Detail |
|-------|--------|
| **Source** | [arxiv.org/abs/2503.19988](https://arxiv.org/abs/2503.19988) |
| **Contains** | Framework that generates CoT preference pairs using execution accuracy as sole feedback. No reward model or human annotations needed. |
| **Key result** | Improves BIRD accuracy from 57.4% to 68.5% |
| **Relevance** | **HIGH** — the methodology IS our self-improving loop. Shows execution feedback alone can generate preference data for DPO training. |

### 7. NVIDIA Nemotron Agentic Suite
| Field | Detail |
|-------|--------|
| **Source** | HF: nvidia/Nemotron-Agentic-v1 + RL variants |
| **Size** | 181K samples (SFT) + RL variants with pass_rate signals |
| **Format** | JSONL |
| **License** | CC-BY-4.0 |
| **Contains** | Multi-turn tool-calling trajectories with decomposition patterns. RL variants include verifiable reward signals. |
| **Relevance** | **HIGH** — scale + RL signals + permissive license. |

### 8. BIRD-Critic / SWE-SQL
| Field | Detail |
|-------|--------|
| **Source** | [github.com/bird-bench/BIRD-CRITIC-1](https://github.com/bird-bench/BIRD-CRITIC-1) |
| **Size** | 600 dev + 200 OOD test across MySQL, PostgreSQL, SQL Server, Oracle |
| **Contains** | SQL diagnostic benchmark — given buggy SQL + user issues, agents must debug. Includes 3 RL-trained models. |
| **Relevance** | **HIGH** — debugging/diagnostic framing maps to real data agent workflows. |

### 9. ReViSQL / BIRD-Verified
| Field | Detail |
|-------|--------|
| **Source** | [arxiv.org/abs/2603.20004](https://arxiv.org/abs/2603.20004) |
| **Size** | 2.5K verified instances |
| **Contains** | Fixes errors in 61.1% of original BIRD Train. RLVR training achieves human-level 93.2% on BIRD. |
| **Relevance** | **HIGH** — proves quality > quantity. The verified dataset is high-value training data. |

### 10. Salesforce APIGen-MT-5k
| Field | Detail |
|-------|--------|
| **Source** | HF: Salesforce/APIGen-MT-5k |
| **Size** | 5K multi-turn trajectories |
| **Contains** | Triple-verified agent data: format checking, function execution + policy check, semantic verification. |
| **Relevance** | **HIGH** — the 3-stage verification pipeline is a reference architecture for our eval layer. |

---

## Tier 3: Useful — Code Agent & RL Infrastructure

### 11. SWE-smith + Trajectories
| Field | Detail |
|-------|--------|
| **Source** | [HF: SWE-bench/SWE-smith](https://huggingface.co/datasets/SWE-bench/SWE-smith) |
| **Size** | 50,137 task instances from 128 repos; 26K trajectories |
| **License** | Open source |
| **Relevance** | MEDIUM-HIGH — multi-step code reasoning with test execution verification. |

### 12. DeepSWE (Together AI / Agentica)
| Field | Detail |
|-------|--------|
| **Source** | [github.com/rllm-org/rllm](https://github.com/rllm-org/rllm) / [HF: agentica-org/DeepSWE-Preview](https://huggingface.co/agentica-org/DeepSWE-Preview) |
| **Size** | 4.5K problems from R2E-Gym |
| **License** | MIT |
| **Contains** | Fully open RL-trained coding agent. No SFT warmup. 59% on SWE-Bench-Verified. |
| **Relevance** | MEDIUM-HIGH — demonstrates pure RL works. Training recipe is a template. |

### 13. AgentGym-RL
| Field | Detail |
|-------|--------|
| **Source** | [github.com/WooooDyy/AgentGym-RL](https://github.com/WooooDyy/AgentGym-RL) |
| **Contains** | Multi-turn RL trajectories across web navigation, search, games. ScalingInter-RL for exploration-exploitation. |
| **Relevance** | MEDIUM-HIGH — directly addresses long-horizon multi-turn RL with process rewards. |

### 14. Nebius SWE-agent-trajectories
| Field | Detail |
|-------|--------|
| **Source** | [HF: nebius/SWE-agent-trajectories](https://huggingface.co/datasets/nebius/SWE-agent-trajectories) |
| **Size** | 80,036 trajectories |
| **License** | CC-BY-4.0 |
| **Relevance** | MEDIUM — large-scale trajectory pattern reference. |

### 15. Spider 2.0
| Field | Detail |
|-------|--------|
| **Source** | [github.com/xlang-ai/Spider2](https://github.com/xlang-ai/Spider2) |
| **Size** | 632 enterprise-grade problems |
| **License** | Open (ICLR 2025 Oral) |
| **Relevance** | MEDIUM-HIGH — enterprise SQL complexity, but needs cloud credentials. |

### 16. gretelai synthetic_text_to_sql
| Field | Detail |
|-------|--------|
| **Source** | [HF: gretelai/synthetic_text_to_sql](https://huggingface.co/datasets/gretelai/synthetic_text_to_sql) |
| **Size** | 105,851 records across 100 domains |
| **License** | Apache 2.0 |
| **Relevance** | MEDIUM — good diversity, permissive license. |

---

## RL Training Infrastructure (Not Datasets, But Needed)

| Tool | What | Relevance |
|------|------|-----------|
| **Prime Intellect Environments Hub** | Community hub for RL environments. "HuggingFace for RL envs." | HIGH — infrastructure for creating our own envs |
| **Agent-R1** | Open-source end-to-end RL for agents. PPO, GRPO, REINFORCE++. | HIGH — the training framework |
| **OpenRLHF** | Scalable agentic RL framework | MEDIUM — standard RLHF infra |
| **rLLM** | Together AI's RL framework (powers DeepSWE) | MEDIUM — alternative to OpenRLHF |

---

## Not Yet Public (Reference Only)

| System | Lab | What | Status |
|--------|-----|------|--------|
| **Universes** | Anthropic | Ultra-realistic long-horizon training environments | Internal, reportedly $1B+ investment |
| **Synthetic RL** | OpenAI | Self-play, simulators, synthetic feedback for RL | Internal |
| **MegaFlow** | Alibaba/Qwen | 20K parallel Docker envs, 800K verifiable tasks | Paper public, infra internal |
| **Forge** | MiniMax | Process reward for long-context agent rollouts, 100K+ scaffolds | Blog public, data internal |

---

## Recommended Data Strategy for Our Agent

### Phase 1: Foundation (use existing data)
1. **SQaLe (517K)** + **gretelai (105K)** — text-to-SQL foundation, execution-validated
2. **TOUCAN-1.5M** — tool-calling capability, MCP-native
3. **Nemotron-Agentic (181K)** — multi-turn decomposition patterns

### Phase 2: Agent-Specific (fine-tune on trajectories)
4. **DataMind-12K** — data analysis agent trajectories (study + replicate format)
5. **BIRD-Interact** — SQL agent interaction data
6. **AWM-1K** — SQL-backed MCP environments for generating our own trajectories

### Phase 3: Self-Improving Loop (RL from our own product)
7. **ExCoT-DPO methodology** — generate preference pairs from execution feedback
8. **ReViSQL approach** — verify and curate our own training data
9. **Agent-R1 / rLLM** — RL training infrastructure
10. Our verification layer generates reward signals → train better versions

### The Flywheel
```
Ship data agent → Users run queries → Verification layer judges correctness
→ (query, trajectory, reward) tuples generated automatically
→ RL training on our own data → Better agent → More users → More data
```

This is exactly what Junyang Lin described and what the big labs are building internally. We can bootstrap it with the public datasets above, then grow it with our own product data.

---

## Sources

All URLs included inline above. Key papers:
- DataMind: ICLR 2026
- BIRD-Interact: ICLR 2026 Oral
- AWM: [arxiv.org/abs/2602.10090](https://arxiv.org/abs/2602.10090)
- ExCoT-DPO: ACL 2025, [arxiv.org/abs/2503.19988](https://arxiv.org/abs/2503.19988)
- ReViSQL: [arxiv.org/abs/2603.20004](https://arxiv.org/abs/2603.20004)
- TOUCAN: [arxiv.org/abs/2510.01179](https://arxiv.org/abs/2510.01179)
- MegaFlow: [arxiv.org/abs/2601.07526](https://arxiv.org/abs/2601.07526)
- Junyang Lin essay: [genaiassembling.substack.com](https://genaiassembling.substack.com/p/what-junyang-lin-saw)
