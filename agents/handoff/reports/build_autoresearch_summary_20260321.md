---
from: Builder
to: Lily + Launcher
date: 2026-03-21
re: autoresearch_supergeneral_20260321.md
---

# AutoResearch for SuperGeneral — Research Summary

## 1. What You Already Have Locally

### Harbor + SkyRL (SkillClaw hackathon)
- **Harbor:** `/Users/lilyzhang/Documents/lilyzhng/Hackathon/SkillClaw_Private/frameworks/harbor/`
  - Full install with Python 3.13 venv
  - Agent evaluation framework — runs evals in containers, generates rollouts in ATIF v1.6 format
  - Supports cloud execution via Modal/Daytona
- **SkyRL:** `/Users/lilyzhang/Documents/lilyzhng/Hackathon/SkillClaw_Private/frameworks/SkyRL/`
  - Full install: skyrl (core), skyrl-train, skyrl-tx, skyrl-agent, skyrl-gym
  - On-policy RL + Harbor sandbox integration (official since Feb 2026)
  - Tinker API for local GPU training
  - You used this before for injection resistance training

### OpenEnv hackathon environment
- **Location:** `/Users/lilyzhang/Documents/lilyzhng/Hackathon/OpenEnv/hackathon/`
- **Four task families:** hand-draw, law, IB, consulting (diamond/hourglass/seesaw/temple)
- **Reward v2:** process signals (0.4) + correctness (0.6) — already fixed the efficiency_mult bug
- **Two GRPO training scripts ready:**
  - `modal_apex_grpo_msswift.py` — ms-swift + QLoRA on Qwen3-Coder-Next (2×B200)
  - `modal_apex_grpo_unsloth.py` — Unsloth + TRL (lighter)
- **Harbor adapter:** exists at `hackathon/harbor_adapter/`
- **Eval harness:** `eval/baseline_eval.py` with 20+ model results

### Autoresearch fork
- **GitHub:** https://github.com/lilyzhng/autoresearch — fork exists
- **NOT cloned locally** — needs `git clone`

---

## 2. RL Environment Comparison

| | **Harbor** | **OpenEnv** | **Atropos (Nous)** | **Prime Intellect** |
|---|---|---|---|---|
| **What** | Agent eval + rollout generation in containers | Gymnasium-style RL interface (reset/step/reward) | RL env for tool-calling trajectories | Async RL at scale (FSDP2 + vLLM) |
| **Reward flexibility** | You define verifiers per env | You define step() returns | Per-environment server | Structured as (dataset, harness, reward) |
| **Autonomous loops** | Good — 1000s of parallel envs | Clean abstraction, maps to standard RL loops | Explicitly designed for trajectory generation at scale | Best for 100+ GPU scale |
| **Training integration** | SkyRL (official), Together.AI | SkyRL, TRL via rollout_func | Tinker API, bring-your-own-trainer | PRIME-RL (tightly coupled) |
| **Tool composition support** | Terminal/bash focus | Generic | **Best** — has tool_calling_server, multi-turn tool-use env | Generic |
| **You already have** | ✅ Installed locally | ✅ Full hackathon env | ❌ Need to set up | ❌ Need to set up |

### My take

**For SuperGeneral auto-research, Atropos is the most interesting new option** — it has a native tool-calling environment server, which is exactly what tool composition needs. But you already have Harbor + SkyRL working and OpenEnv with four task families.

**Practical recommendation:** Start with what works. Your Harbor + SkyRL + OpenEnv stack is already set up. Write the `program.md` for that stack first, get the loop running, then evaluate if Atropos gives you something Harbor doesn't.

---

## 3. Sandbox Comparison

| | **Modal** | **E2B** | **Daytona** |
|---|---|---|---|
| **Isolation** | gVisor | Firecracker microVMs | Docker |
| **Startup** | Sub-second | ~200ms | Sub-90ms |
| **Cost** | ~$0.14/hr/core, 3x for sandbox | $0.05/hr/vCPU | $200 free compute |
| **Key strength** | You already use it. Same platform as training = no data movement | Best SDK, purpose-built for AI agents | Persistent state across sessions |
| **Key weakness** | 3x sandbox premium | No GPU access | Docker isolation weaker |

### My take

**Modal is the obvious choice.** You already use it for training, Harbor supports it, and keeping sandbox + training on the same platform eliminates data movement overhead. The 3x sandbox premium matters at scale but not for initial experiments.

---

## 4. Recommended Stack for Auto-Research Loop

```
program.md (Karpathy-style)
    ↓
Agent modifies environment/reward code
    ↓
Harbor runs eval in Modal sandbox
    ↓
Objective metric: task completion rate + composition correctness
    ↓
Keep/discard based on metric
    ↓
LOOP FOREVER
```

**Environment:** Your existing OpenEnv hackathon env (Harbor-compatible)
**Sandbox:** Modal (already set up)
**Training (if needed):** SkyRL + Harbor (already integrated)
**Objective metric:** Task completion rate across the 4 task families

---

## 5. Next Steps

1. **Clone autoresearch fork locally** — `git clone git@github.com:lilyzhng/autoresearch.git`
2. **Read Karpathy's program.md** — understand the loop structure
3. **Write a program.md for SuperGeneral** — define:
   - What the agent can modify (environment code? reward function? task specs?)
   - What it cannot touch (eval harness, task families)
   - Objective metric (task completion rate across models)
   - Experiment time budget per iteration
4. **Wire up the loop** — Harbor eval → metric → keep/discard → next experiment
5. **Run it overnight** — see what it finds

### Open question for Lily

What should the agent be allowed to modify?
- **Option A:** Environment code (reward function, tool definitions, workspace structure) — optimizing the environment
- **Option B:** Agent strategy (prompt, tool selection, composition approach) — optimizing the agent
- **Option C:** Both — but this is a much larger search space

Karpathy's autoresearch only modifies `train.py`. We need to pick our equivalent.
