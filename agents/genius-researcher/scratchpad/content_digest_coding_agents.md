# Content Digest: Coding Agent Fine-Tuning (2026)

**Source:** `agents/handoff/reports/research_coding_agent_finetuning_20260325.md`
**Generated:** 2026-03-25

---

## Tweet Options

### Tweet 1 (cost angle)
The best open-source coding agent scores 54.2% on SWE-bench for $2K training cost. That's 57x cheaper than the next method. The secret: skip RL entirely — use Soft Verified Generation on synthetic bugs. Patches don't even need to be fully correct. [AI2 SERA]

### Tweet 2 (contrarian angle)
Everyone's racing to scale RL for coding agents. But the data says: a 24B model with good SFT data (68% SWE-bench) beats a 235B model with mediocre data (61.7%). Data quality > model size > training method. The 32B sweet spot is real.

### Tweet 3 (benchmark integrity angle)
OpenAI's contamination audit found ALL frontier models leak training data on SWE-bench Verified. Every leaderboard score you've seen is inflated. SWE-bench Pro is now the only rigorous benchmark — and most teams haven't published scores on it yet.

---

## Twitter/X Thread (5 tweets)

**1/5**
We surveyed 15 approaches to fine-tuning coding agents in 2026. Open-weight models went from 30% to 71% on SWE-bench in 12 months. Here's what actually works (and what's overhyped):

**2/5**
The winning recipe is SFT on curated trajectories + RL refinement. But the surprise: AI2's SERA skips RL entirely. Using "Soft Verified Generation" — where training patches only need to be *partially* correct — they hit 54.2% for just $2K. That's 57x cheaper than alternatives.

**3/5**
Pure RL works (DeepSWE: 59% with test-time scaling) but costs 64 H100s for 6 days. The real unlock is test-time scaling: DeepSWE jumps from 42% to 59% just by sampling 16 times + verification. Invest in verifiers, not just training.

**4/5**
The 32B model size is the sweet spot. Fits on consumer GPUs, big enough for multi-file reasoning, small enough for practical RL. But watch MoE: Qwen3-Coder-Next (80B total, 3B active) hits 71.3% while being inference-efficient. Sparse is the future.

**5/5**
The elephant in the room: SWE-bench Verified is contaminated. All frontier models show data leakage. And the biggest gap isn't benchmarks — it's multi-language support (everything is Python-only) and long-horizon tasks. Nobody's training agents for multi-day refactors yet.

---

## Executive Summary

- **Open-weight coding agents surged from ~30% to 71% on SWE-bench Verified in under 12 months**, with 32B models emerging as the efficiency sweet spot and MoE architectures (Qwen3-Coder-Next, 80B/3B active) pointing to the future.
- **The most cost-effective method is AI2's Soft Verified Generation (SVG):** 54.2% SWE-bench for ~$2K training cost — 57x cheaper than comparable approaches — by training on partially-correct synthetic patches instead of requiring full correctness.
- **SFT + RL hybrid is the pragmatic winner**, but test-time scaling (sampling multiple solutions + verification) is the great equalizer, boosting DeepSWE from 42.2% to 59% without any additional training.
- **Data quality decisively beats data quantity:** two-stage filtering on trajectories consistently outperforms training on larger unfiltered datasets, and a 24B model with clean data (Devstral, 68%) outperforms a 235B model with noisier data (Nebius, 61.7%).
- **Critical caveat: SWE-bench Verified is contaminated.** OpenAI's audit found training data leakage across all frontier models. SWE-bench Pro is now the recommended rigorous benchmark, and most teams have not yet reported scores on it.
