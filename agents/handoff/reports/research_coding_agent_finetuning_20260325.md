# Best Approaches for Fine-Tuning Coding Agents (2026)

**Author:** Genius Researcher | **Date:** 2026-03-25 | **Status:** Complete
**Method:** /auto-research pipeline live test

## Executive Summary

The coding agent fine-tuning landscape has converged on a clear pattern: **SFT on curated trajectories followed by RL refinement** yields the best open-weight results, with 32B models emerging as the efficiency sweet spot. Frontier closed models (Claude Opus 4.5, GPT-5.2) now exceed 80% on SWE-bench Verified, while open-weight agents have surged from ~30% to 59-71% in under 12 months. The most cost-effective breakthrough is AI2's Soft Verified Generation (SVG), which matches RL-trained models at 57x lower cost using only SFT.

**Important caveat:** OpenAI's contamination audit found that all frontier models show training data leakage on SWE-bench Verified. SWE-bench Pro is now the recommended rigorous benchmark.

## Top Approaches by SWE-bench Verified Score

| Rank | Method/Model | Base Model | SWE-bench Verified | Training Method | Training Cost | Paper/Source |
|------|-------------|------------|-------------------|----------------|---------------|-------------|
| 1 | Claude Opus 4.5 (closed) | Proprietary | 80.9% | Unknown (proprietary) | N/A | [Leaderboard](https://llm-stats.com/benchmarks/swe-bench-verified) |
| 2 | Qwen3-Coder-Next | 80B (3B active MoE) | 71.3% (w/ OpenHands) | Agent RL + long-horizon RL | 20K parallel envs | [Qwen Blog](https://qwenlm.github.io/blog/qwen3-coder/) |
| 3 | Devstral Small 2 | 24B | 68.0% | SFT on agent trajectories | Not disclosed | [Mistral](https://mistral.ai/news/devstral-2-vibe-cli) |
| 4 | DeepSWE (TTS) | Qwen3-32B | 59.0% (Pass@16 71%) | Pure RL (GRPO++) | 64 H100s x 6 days | [Together AI](https://www.together.ai/blog/deepswe) |
| 5 | SERA-32B (64K ctx) | Qwen 2.5 Coder 32B | 54.2% | SFT with SVG | ~$2K / 40 GPU-days | [AI2](https://allenai.org/blog/open-coding-agents) |
| 6 | Devstral Small 1.1 | 24B | 53.6% | SFT on SWE-Gym trajectories | Not disclosed | [Mistral](https://mistral.ai/news/devstral) |
| 7 | R2E-Gym | Qwen 2.5 Coder 32B | 51.0% | SFT + hybrid test-time scaling | Not disclosed | [R2E-Gym](https://r2e-gym.github.io/) |
| 8 | SERA-32B (32K ctx) | Qwen 2.5 Coder 32B | 49.5% | SFT with SVG | ~$400 to reproduce | [AI2](https://allenai.org/papers/opencodingagents) |
| 9 | Nebius RFT (235B) | Qwen3-Coder-480B | 61.7% | Rejection fine-tuning | Not disclosed | [Nebius](https://nebius.com/blog/posts/openhands-trajectories-with-qwen3-coder-480b) |
| 10 | Nebius RFT (30B) | Qwen3-Coder-480B distill | 50.3% | Rejection fine-tuning | Not disclosed | [Nebius](https://nebius.com/blog/posts/openhands-trajectories-with-qwen3-coder-480b) |
| 11 | DeepSWE (Pass@1) | Qwen3-32B | 42.2% | Pure RL (GRPO++) | 64 H100s x 6 days | [Together AI](https://www.together.ai/blog/deepswe) |
| 12 | SWE-agent-LM-32B | Qwen 2.5 Coder 32B | 40.2% | GRPO RL via SkyRL | Not disclosed | [SWE-smith](https://swesmith.com/) |
| 13 | SA-SWE-32B | Qwen3-32B | 39.4% | Pure RL via SkyRL-Agent | 2x cheaper than peers | [SkyRL-Agent](https://arxiv.org/abs/2511.16108) |
| 14 | OpenHands-LM-32B | Qwen 2.5 Coder 32B | 37.0% | SFT via SWE-Gym | Not disclosed | [SWE-Gym](https://github.com/SWE-Gym/SWE-Gym) |
| 15 | RepoForge-8B | 8B | 17.4% | SFT then RL | Minimal (automated pipeline) | [RepoForge](https://arxiv.org/abs/2508.01550) |

## Training Methodology Comparison

### SFT Approaches

**Trajectory-based SFT** remains the foundation of most open-weight coding agents. The core idea: run a strong model (e.g., Claude 3.7 Sonnet, Qwen3-Coder-480B) as an agent, collect successful trajectories solving real GitHub issues, then fine-tune a smaller model on those trajectories.

Key results:
- **SWE-agent-LM-32B**: Fine-tuned Qwen 2.5 Coder 32B on just 5K trajectories from Claude 3.7 Sonnet, achieving 40.2% on SWE-bench Verified
- **Devstral**: Trained on SWE-Gym trajectories using OpenHands CodeAct scaffold, hitting 46.8% (v1) to 68.0% (Small 2)
- **SERA-32B (SVG)**: The cost-efficiency champion. Instead of requiring fully correct patches, SVG uses "soft verification" -- patches only need to be partially correct. Uses a menu of 51 synthetic bug patterns. Achieves 54.2% for ~$2K total cost
- **Rejection Fine-Tuning (RFT)**: Nebius generated 67K trajectories from Qwen3-Coder-480B, filtered by quality, achieving 50.3% (30B) and 61.7% (235B)

**Key insight:** Quality filtering matters more than quantity. Two-stage filtering (broad heuristic filter -> strict correctness filter) consistently outperforms training on unfiltered data.

### RL Approaches

**Pure RL from base models** has emerged as a viable alternative to SFT, with DeepSWE proving you can train a competitive agent using only RL.

Key results:
- **DeepSWE (GRPO++)**: Pure RL on Qwen3-32B, no SFT warmup. 42.2% Pass@1, 59% with test-time scaling. Trained on 4.5K R2E-Gym problems. Key innovation: GRPO++ algorithm (no KL loss, no entropy loss, clip high for exploration, length normalization)
- **DeepCoder-14B (GRPO+)**: Achieved 60.6% on LiveCodeBench, 92.6% on HumanEval+. Key innovation: iterative context lengthening (train at 32K, generalize to 64K), async pipelined sampling for 2.5x speedup
- **SkyRL / SA-SWE-32B**: Pure RL framework achieving 39.4% Pass@1. Key innovation: AST-based search tool integration during training, async pipeline dispatcher with 1.55x speedup
- **Qwen3-Coder Agent RL**: Long-horizon RL with 20,000 parallel environments on Alibaba Cloud. Results: 71.3% on SWE-bench Verified

**Key insight:** Pure RL works but requires massive compute (64+ H100s). The gap between RL and SFT narrows significantly when you add test-time scaling (voting, verification). RL's real advantage is emergent behaviors: models learn edge case testing and adaptive reasoning without being taught.

### SFT + RL Hybrid Approaches

The **SFT-then-RL** pipeline consistently outperforms either approach alone.

Key results:
- **RepoForge-8B**: SFT warmup on curated trajectories, then binary-reward RL on 160 instances the teacher model already solved. 17.4% at just 8B params -- SOTA for sub-8B models
- **SWE-smith -> SkyRL pipeline**: SFT on SWE-smith synthetic data, then GRPO RL refinement. The SFT phase provides stable starting behavior; RL refines and sharpens

**Key insight:** RL on top of SFT is cheaper and more stable than pure RL. The SFT phase gives the model "vocabulary" for the task; RL teaches it to actually solve problems.

### Self-Play Approaches

**Self-Play SWE-RL** (December 2025) represents the most radical departure: no human-curated data at all.

- The agent iteratively injects bugs into real codebases, then learns to repair them
- Bugs specified by test patches (not natural language), enabling fully automated curriculum
- Results: +10.4 points on SWE-bench Verified, +7.8 on SWE-bench Pro over baseline
- Consistently outperforms human-data-trained baselines despite never seeing natural language issues during training

**Key limitation:** Self-play agents struggle with natural language skill acquisition. They get good at code manipulation but may miss nuances in human-written issue descriptions.

## Data Strategy Comparison

### Synthetic Trajectories

**SWE-smith** (NeurIPS 2025 Spotlight): Given any Python codebase, automatically synthesizes 100s-1000s of task instances that break existing tests. Created 50K instances from 128 repos. SWE-agent-LM-32B trained on this data: 40.2%.

**SERA SVG**: Uses 51 synthetic bug patterns as a "menu" to generate diverse training scenarios. 57x cheaper than SWE-smith. Key insight: patches don't need to be fully correct -- partially correct patches still teach useful behavior.

**SWE-Playground**: Generates entire projects and tasks from scratch using strong LLMs, eliminating reliance on real repos.

**Scaling results:**
- Qwen 2.5 Coder 7B: 0/300 -> 20/300 with only 800 synthetic samples
- Qwen 2.5 Coder 32B: 4/300 -> 25/300
- Synthetic-trained models outperform larger baselines (72B) even with 40% unreviewed data

### Real-World Trajectories

**SWE-Gym** (ICML 2025): 2,438 real Python task instances with executable environments. The gold standard for training environments. Used to train OpenHands-LM-32B (37%).

**R2E-Gym**: 8.1K problems generated from real commits via SWE-Gen pipeline. Hybrid verifiers enable 51% on SWE-bench Verified -- first open-weight model competitive with proprietary (o1, Sonnet 3.5 v2).

**Nebius OpenHands trajectories**: 67K trajectories from running Qwen3-Coder-480B on real GitHub issues. Two-stage quality filtering.

### Hybrid Approaches

The **best results combine synthetic environment generation with real-world trajectory collection**:

1. **R2E-Gym + DeepSWE**: Synthetic environments from R2E-Gym, RL training produces DeepSWE at 59%
2. **SWE-smith + SkyRL**: Synthetic tasks for SFT warmup, then RL refinement
3. **RepoForge**: Automated pipeline generates environments from real commits, then runs SFT + RL

**The meta-pattern:** Use synthetic data for breadth (many diverse tasks cheaply), real trajectories for depth (high-quality solutions to hard problems), and RL for refinement.

## Model Architecture & Size Analysis

### The 32B Sweet Spot

Nearly every open-weight coding agent uses **Qwen 2.5 Coder 32B** or **Qwen3-32B** as the base model. This is not coincidental:

- Fits on a single node of consumer/prosumer GPUs (24-48GB VRAM)
- Large enough to handle multi-file, multi-step reasoning
- Small enough for practical RL training (DeepSWE: 64 H100s x 6 days)
- Qwen's code-specific pretraining provides strong foundation

### MoE as the Next Frontier

**Qwen3-Coder-Next** (80B total, 3B active) demonstrates that MoE can achieve 71.3% while being inference-efficient. This suggests the future is large sparse models, not large dense models.

### Small Models Catching Up

- **RepoForge-8B**: 17.4% at 8B params shows small models can be viable
- **Devstral Small 2 (24B)**: 68.0% -- competitive with models 5x its size
- The gap between 24B and 32B is narrowing, especially with better training data

### Size vs. Method

| Model Size | Best SWE-bench Verified | Method |
|-----------|------------------------|--------|
| 8B | 17.4% (RepoForge) | SFT + RL |
| 24B | 68.0% (Devstral Small 2) | SFT on trajectories |
| 32B | 59.0% (DeepSWE w/ TTS) | Pure RL |
| 80B MoE (3B active) | 71.3% (Qwen3-Coder-Next) | Agent RL |
| 235B+ | 61.7% (Nebius RFT) | Rejection fine-tuning |

## Key Insights

1. **SFT is no longer enough, but it's still necessary.** Pure RL (DeepSWE) works but is expensive. The pragmatic path is SFT warmup + RL refinement. SVG offers a radical cost reduction for the SFT phase.

2. **Test-time scaling is the great equalizer.** DeepSWE jumps from 42.2% (Pass@1) to 59% (Pass@16 + hybrid verification). Investing in verifiers may be more cost-effective than better training.

3. **32B is the practical sweet spot for open-weight agents.** It balances capability, training cost, and inference speed. MoE architectures (Qwen3-Coder-Next at 80B/3B active) are the next evolution.

4. **Data quality trumps data quantity.** SERA-32B matches much more expensive approaches by being smart about data generation (SVG). Two-stage filtering consistently helps.

5. **Self-play is the dark horse.** Self-Play SWE-RL eliminates human data dependency entirely. Current limitations (weak NL understanding) are likely solvable with hybrid approaches.

6. **The agent scaffold matters as much as the model.** OpenHands CodeAct, SWE-agent, and Mini-SWE-Agent produce very different results with the same underlying model. Tool integration during training (SkyRL's AST tool) improves RL outcomes.

7. **SWE-bench Verified is contaminated.** All frontier models show data leakage. SWE-bench Pro and SWE-rebench are becoming the new standard for rigorous evaluation.

## Gap Analysis

1. **No consensus on RL algorithm.** GRPO, GRPO+, GRPO++, REINFORCE, PPO -- every team uses a different variant. Head-to-head comparisons are rare. The field needs standardized ablations.

2. **Multi-language support is weak.** Almost all training environments are Python-only. JavaScript, TypeScript, Java, Rust, and Go are underrepresented in training data.

3. **Long-horizon tasks remain hard.** Most training tasks are single-PR fixes. Multi-PR, multi-day refactoring tasks have no good training signal.

4. **Cost reporting is inconsistent.** Some report GPU-hours, some report dollar costs, some report nothing. Reproducibility suffers.

5. **Real-world deployment gap.** SWE-bench tasks are well-scoped issue fixes. Real coding work includes design, review, debugging, and communication -- none of which are captured.

6. **No good reward model for coding.** Binary pass/fail on tests is crude. Process reward models for code are almost nonexistent. This limits RL effectiveness.

7. **Self-play + NL integration is unexplored.** Combining self-play's data efficiency with natural language grounding could yield much stronger agents.

## Sources

### Papers & Technical Reports
- [SERA: Soft-Verified Efficient Repository Agents (AI2, Jan 2026)](https://arxiv.org/html/2601.20789v1)
- [SWE-smith: Scaling Data for SWE-agents (NeurIPS 2025)](https://arxiv.org/abs/2504.21798)
- [DeepSWE: Training a Fully Open-sourced Coding Agent by Scaling RL (Together AI, Jul 2025)](https://www.together.ai/blog/deepswe)
- [SWE-Gym: Training Software Engineering Agents and Verifiers (ICML 2025)](https://arxiv.org/abs/2412.21139)
- [R2E-Gym: Procedural Environments and Hybrid Verifiers (COLM 2025)](https://arxiv.org/abs/2504.07164)
- [Self-Play SWE-RL: Toward Training Superintelligent Software Agents (Dec 2025)](https://arxiv.org/abs/2512.18552)
- [SkyRL-Agent: Efficient RL Training for Multi-turn LLM Agent (Nov 2025)](https://arxiv.org/abs/2511.16108)
- [RepoForge: Training a SOTA Fast-thinking SWE Agent (Aug 2025)](https://arxiv.org/abs/2508.01550)
- [Agent-R1: Training Powerful LLM Agents with End-to-End RL (Nov 2025)](https://arxiv.org/html/2511.14460v1)
- [Devstral: Fine-tuning Language Models for Coding Agent Applications (Mistral, Sep 2025)](https://arxiv.org/pdf/2509.25193)
- [Qwen3-Coder-Next Technical Report (Mar 2026)](https://arxiv.org/pdf/2603.00729)
- [DeepCoder-14B / rLLM framework](https://topmostads.com/deepcoder-14b-open-source/)

### Leaderboards & Benchmarks
- [SWE-bench Verified Leaderboard](https://llm-stats.com/benchmarks/swe-bench-verified)
- [SWE-rebench Leaderboard](https://swe-rebench.com/)
- [SWE-bench Pro (Scale Labs)](https://labs.scale.com/leaderboard/swe_bench_pro_public)

### Model Cards & Code
- [allenai/SERA-32B on HuggingFace](https://huggingface.co/allenai/SERA-32B)
- [SWE-bench/SWE-agent-LM-32B on HuggingFace](https://huggingface.co/SWE-bench/SWE-agent-LM-32B)
- [R2E-Gym GitHub](https://github.com/R2E-Gym/R2E-Gym)
- [SWE-Gym GitHub](https://github.com/SWE-Gym/SWE-Gym)
- [SWE-smith GitHub](https://github.com/SWE-bench/SWE-smith)
- [Nebius OpenHands Trajectories (67K)](https://nebius.com/blog/posts/openhands-trajectories-with-qwen3-coder-480b)
