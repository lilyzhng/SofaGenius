---
date: 2026-03-22
query: "multi-step, multi-turn workflow datasets for RL agent training — real data, open-ended bash/python actions"
---

# Multi-Step Workflow Datasets — Research Report

## Tier 1: Highest Relevance

### 1. CoderForge-Preview (Together AI)
- **HF:** [togethercomputer/CoderForge-Preview](https://huggingface.co/datasets/togethercomputer/CoderForge-Preview)
- **Size:** 258K trajectories (155K test-verified retained for SFT)
- **Tasks:** Long-horizon SWE — bug fixes, feature implementations from real GitHub repos
- **Real/Synthetic:** Real tasks, agent-generated trajectories (Qwen3-Coder-480B + rejection sampling)
- **Steps:** Up to 128K tokens per trajectory
- **License:** Open
- **Why:** Largest open test-verified coding agent dataset. Qwen3-32B: 23% → 59.4% on SWE-bench Verified.

### 2. SWE-rebench / V2 (Nebius)
- **HF:** [nebius/SWE-rebench](https://huggingface.co/datasets/nebius/SWE-rebench)
- **Size:** 21K+ tasks from 3,400+ GitHub repos. Also: [80K+ OpenHands trajectories](https://huggingface.co/datasets/nebius/SWE-rebench-openhands-trajectories)
- **Tasks:** Real GitHub issue resolution
- **Real/Synthetic:** Real GitHub PRs
- **Steps:** Multi-turn, each task has Docker container
- **License:** Apache 2.0
- **Why:** Designed for RL training. Largest real-world SWE task collection.

### 3. APEX-Agents (Mercor) — already using
- **HF:** [mercor/apex-agents](https://huggingface.co/datasets/mercor/apex-agents) (480) + [APEX-v1-extended](https://huggingface.co/datasets/mercor/APEX-v1-extended) (100)
- **Tasks:** Professional services — IB, consulting, law, medical
- **Real/Synthetic:** Created by real professionals
- **Why:** Only dataset with real professional domain tasks. Open-ended bash/python + file processing.

### 4. R2E-Gym (Agentica)
- **HF:** [R2E-Gym](https://huggingface.co/R2E-Gym)
- **Size:** 8,100+ problems across 13 repos
- **Tasks:** Code editing, test generation, patch verification
- **Real/Synthetic:** Real repo states, synthetic task generation
- **License:** MIT
- **Why:** Powers DeepSWE (59% SWE-bench Verified). Gym-style RL interface. Has pre-collected SFT trajectories.

### 5. DABStep (Adyen + HuggingFace)
- **HF:** [adyen/DABstep](https://huggingface.co/spaces/adyen/DABstep)
- **Size:** 450+ tasks
- **Tasks:** Real financial data analysis — multi-step Python/code over heterogeneous data
- **Real/Synthetic:** **Real** — from Adyen's actual analytics workloads
- **Why:** Real financial domain. Best agents only 16% accuracy. Requires code + contextual reasoning.

### 6. GAIA / GAIA2 (Meta)
- **HF:** [gaia-benchmark/GAIA](https://huggingface.co/datasets/gaia-benchmark/GAIA) (450+) + [GAIA2](https://huggingface.co/datasets/meta-agents-research-environments/gaia2) (800)
- **Tasks:** Real-world multi-step reasoning — web browsing, file processing, code execution
- **Real/Synthetic:** Curated real-world questions
- **License:** CC-BY-4.0
- **Why:** Gold standard for general-purpose agent eval. 3 difficulty levels.

## Tier 2: Strong Relevance

### 7. AgentGym-RL (ICLR 2026 Oral)
- **HF:** [AgentGym/AgentGym-RL-Data-ID](https://huggingface.co/datasets/AgentGym/AgentGym-RL-Data-ID)
- **Size:** 14 environments, 27 tasks
- **Tasks:** Web navigation, text games, programming, tool-using
- **License:** Apache 2.0
- **Why:** First unified RL framework for multi-environment agent training. ScalingInter-RL.

### 8. OpenHands/Nebius Trajectories
- **Size:** 67K trajectories
- **Tasks:** SWE tasks via CodeAct (bash + Python)
- **Why:** 3x more successful attempts. 50.3% (30B) on SWE-bench Verified.

### 9. SWE-smith + trajectories (Princeton NLP)
- **HF:** [SWE-bench/SWE-smith](https://huggingface.co/datasets/SWE-bench/SWE-smith) (50K tasks) + [trajectories](https://huggingface.co/datasets/SWE-bench/SWE-smith-trajectories) (5K)
- **License:** MIT
- **Why:** Produced SWE-agent-LM-32B (40.2% SWE-bench Verified). Executable Docker environments.

### 10. RepoForge
- **Size:** 7,304 executable environments
- **Tasks:** SWE — autonomous end-to-end pipeline
- **Why:** 14x storage reduction, 19,000x cheaper labeling.

### 11. InterCode (NeurIPS 2023)
- **Size:** 5 environments (Bash, Python, SQL, CTF, SWE)
- **License:** MIT
- **Why:** Pioneer interactive coding RL environment. Gym-style interface.

### 12. DA-Code (EMNLP 2024)
- **HF:** [Jianwen2003/DA-Code](https://huggingface.co/datasets/Jianwen2003/DA-Code)
- **Size:** 500 tasks
- **Tasks:** Data science — wrangling, ML, EDA
- **Why:** Best agents only 30.5%. Real data science tools.

## Key Findings

**For professional domains:** APEX is still the best. DABStep complements for financial data analysis. No equivalent for legal/medical/consulting beyond APEX.

**For training scale:** CoderForge-Preview (155K verified trajectories) + SWE-rebench (21K tasks + 80K trajectories) give the most volume.

**For RL training framework:** AgentGym-RL is purpose-built for multi-environment RL.

**Gap:** Professional domain datasets beyond SWE are extremely rare. APEX is basically the only one. Financial data analysis has DABStep. Legal, medical, consulting have nothing else at scale.
