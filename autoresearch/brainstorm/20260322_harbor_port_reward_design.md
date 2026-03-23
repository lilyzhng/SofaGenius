# Brainstorm: Harbor Port + Reward Design for APEX RL Training

**Date:** 2026-03-22
**Participants:** Lily + CC Builder

---

## 背景

我们在讨论如何把 SuperGeneral building-block environment 从 OpenEnv port 到 Harbor，用于 RL 训练 professional agent tasks。讨论过程中发现了几个关键的设计问题需要解决。

---

## 对话 1: RL Environment 基础概念

### Training Environment vs Evaluation Benchmark

- RL environment 分 training 和 evaluation，但关键区分是：**environment（基础设施）是共享的，tasks（具体任务）才需要分开**
- Training tasks: agent 在这些任务上 rollout、拿 reward、学习
- Eval tasks: held-out 的任务，agent 从没见过，测 generalization
- **Split 的是 tasks，不是 data。** RL 不是先生成数据再 split（那是 supervised learning）。RL 是 agent 通过跟 environment live interaction 来学习，数据是 on-the-fly 产生的。

### 自然的 Train/Eval Split（License 决定的）

| Dataset | Tasks | License | 用途 |
|---------|-------|---------|------|
| APEX-v1-extended | 100 | CC-BY-4.0 ✅ | Training |
| apex-agents | 480 | Eval-only ❌ | Evaluation |

---

## 对话 2: OpenEnv vs Harbor vs ClawEval

### 三个框架的本质区别

**OpenEnv (Gymnasium-style)**
- 来自 robotics/game RL 的传统
- 核心：Python class with `reset()` / `step(action)` → (observation, reward, done, info)
- 一切都是 Python 对象。Agent 在 Python sandbox 里「模拟」做事
- 为 Atari/机器人/棋盘游戏设计 — action space 固定
- Lily 已经用它建了完整的 ApexEnvironment

**Harbor**
- Agent 直接在真实 Linux container 里打 bash commands
- 没有 `step()` function，没有 Python 抽象层
- Task = 一个文件夹: `instruction.md` + `Dockerfile` + `tests/test.sh`
- 天然 bash-native, multi-turn, isolated
- 官方 SkyRL integration (HarborGenerator)
- **核心优势：对 coding/professional agent 更自然**

**ClawEval**
- 外部 benchmark/leaderboard，跟我们的工作无关
- Lily 之前审计过发现 pass³ metric 有 bug，已 move on

### 决策：Port 到 Harbor

**Gymnasium = agent 在 Python sandbox 里「模拟」做事**
**Harbor = agent 在真实 Linux 里「真的」做事**

Lily 做的 ApexEnvironment = environment design（tasks, rewards, tool definitions）= 菜谱
Harbor = infrastructure layer（Docker isolation, parallel rollouts, RL pipeline）= 厨房

Port = 保留核心设计，让 Harbor 干脏活。

### 关于 contribute OpenEnv 的决定

**不值得。** 原因：
1. Environment design 是 Lily 的 IP
2. OpenEnv 的 Gymnasium-style 方向可能被 bash-native 方案取代
3. Maintainer 夸你有意思 ≠ 有回报
4. 时间应该花在建自己的东西上

---

## 对话 3: 现有工作盘点

### 已完成的 APEX 工作 (Hackathon/OpenEnv/)

- ✅ 数据分析 — 两个 dataset 分析完毕
- ✅ 数据转换 — GRPO format + Harbor format 转换器都写好了
- ✅ Environment 实现 — 完整 ApexEnvironment (models, bash executor, task loader, reward)
- ✅ 9-Model Baseline Eval — GPT-4o-mini, DeepSeek-V3, Kimi-K2, Claude Opus 等
- ✅ Training Scripts — 两条路径:
  - `modal_grpo.py` — Option B: real env rollout, reward from env (process signals + correctness)
  - `modal_grpo_proxy.py` — Option A: 4 proxy reward functions, no env interaction

### HuggingFace 上的数据

| Dataset | Tasks | 用途 |
|---------|-------|------|
| `lilyzhng/apex-grpo-tool-calling` | 480 | 已转 GRPO format，有 rubric_keywords |
| `lilyzhng/apex-multiturn-toolcalling` | 100 | Multi-turn rollouts，可做 reward validation |
| `lilyzhng/terminal-bench-rollouts` | 3 | Harbor format rollout 数据 |
| `mercor/APEX-v1-extended` | 100 | 训练用，`documents/` 有 PDFs，CC-BY-4.0 |
| `mercor/apex-agents` | 480 | Eval-only，`world_files_zipped/` 有 33 个 world zips (gated) |

### File Attachments 都可以下载

- **v1-extended**: `documents/` 目录，免费下载
- **apex-agents**: `world_files_zipped/` + `task_files/`，gated access（同意条款后可下载）
- **所有 480 个 eval tasks 都能完整支持**，包括那 175 个需要 file attachments 的

---

## 对话 4: APEX 数据形态深度分析

### APEX 不是 Tool Calling Dataset

每个 task = professional 问题 + PDF/Excel/CSV 附件 + rubric（评分标准）

**真实 task 例子：**
- Legal: "Tesla 碰撞案在 Florida 能不能追回 diminished value?" + 法律 PDF + 10 criteria
- Finance: "做 LBO analysis，算 IRR、MOIC、GP carry" + Excel 模型 + 10 criteria
- Medical: "13 个月小孩疫苗落后了，今天打什么?" + AAP 免疫日程 PDF + 9 criteria
- Consulting: "砍掉 30% 最差 campaigns 能省多少钱?" + CSV 数据 + 7 criteria

**没有 function call schemas，没有 MCP tool definitions。** Agent 需要的 "tools" = bash + python + 文件处理。

### Building Block Tools 的问题

Lily 之前在 professional_env.py 里的 domain-specific tools (royalty_calc.py, market_sizing.py) 是 **hackathon demo 用的 toy tools，不来自 APEX 数据本身**。

**APEX tasks 不需要 hardcoded domain tools。** Agent 用 bash + python 自己解决。从 eval 日志看，Claude Sonnet 做 law task 时自己创建了 analysis.py — 这本身就是 tool creation。

---

## 对话 5: Reward Design — 三个流派（关键讨论）

### 流派对比

| 流派 | 做法 | 优点 | 缺点 | 代表 |
|------|------|------|------|------|
| **A. Formal tool calling** | 定义 tool schemas，验证 function call 参数 | 容易验证 | **限制 agent 自由度** ❌ | ToolBench, Gorilla, BFCL |
| **B. Bash + outcome only** | 给 bash，只看结果 | Agent 完全自由 | **Reward 太 sparse** ❌ | Harbor, Terminal-Bench |
| **C. Bash + process signals (Hybrid)** | 给 bash，看结果 + 看过程 | **Agent 自由 + 训练高效** ✅ | 需要设计 process signals | **Agent-R1, VerlTool, ToolRL** |

### 关键论文发现

1. **ToolRL** (arxiv 2504.13958): 分解 reward（format + tool name + param + value）比 binary outcome **高 17%**。Dynamic scaling: 训练早期重 format，后期重 correctness。
2. **VerlTool** (arxiv 2509.01055): 如果**不加 tool use 激励，agent 会自发停止使用 tools**（tool abandonment）。不同 domain 需要不同的 process signals。
3. **ReasonRAG** (arxiv 2505.14069): Process-supervised RL 比 outcome-only RL **效率高 18 倍**。
4. **Agent-R1** (arxiv 2511.14460): 混合 reward = terminal outcome + intermediate process events。Extended MDP 区分 agent actions vs environment transitions。

### 我们的方案 ≈ Agent-R1

Lily 的 building-block environment 设计跟 Agent-R1 最接近：

**Agent-R1:**
```
R = rf (terminal outcome) + rp (intermediate process events) + 0 (otherwise)
```

**Lily 的设计:**
```
R = correctness (outcome) + process signals (tool use/composition/creation) + talk penalty
```

差异：Agent-R1 用 extended MDP，Lily 用 per-step criteria feedback。核心理念一致。

### 决策

- **用 APEX 数据 + bash + process signals（流派 C）**
- **加 tool engagement bonus (+0.05)**，防止 tool abandonment（VerlTool 建议）
- **Process signals 适配 APEX:**
  - Tool use = agent 是否读了 data/ 里的 PDF/Excel
  - Tool composition = 是否结合了 2+ 个数据源
  - Tool creation = 是否创建了新的 .py 或 .sh 脚本
- **需要深入研究 Agent-R1, ToolRL, VerlTool 的具体实现**

---

## 待研究（Next Steps）

### Repos to Study

1. **Agent-R1** — `https://github.com/0russwest0/Agent-R1.git`
   - 重点看：intermediate process events 怎么定义，credit assignment 怎么做
   - Paper: https://arxiv.org/abs/2511.14460

2. **ToolRL** — `https://github.com/qiancheng0/ToolRL.git`
   - 重点看：decomposed reward 设计，dynamic scaling 实现
   - Paper: https://arxiv.org/abs/2504.13958

3. **VerlTool** — `https://github.com/TIGER-AI-Lab/verl-tool.git`
   - 重点看：tool abandonment 的数据，domain-specific tuning
   - Paper: https://arxiv.org/abs/2509.01055

### Open Questions

1. Agent-R1 的 extended MDP 具体怎么实现？能不能直接用在 Harbor + SkyRL 里？
2. ToolRL 的 dynamic reward scaling 怎么接进 GRPO training loop？
3. VerlTool 的 tool engagement bonus 具体是加在哪一步？
4. 我们的 process signals 在 Harbor 里怎么实现？（Harbor test.sh 只跑一次 at the end，不是 per-step）

---

## 对话 6: 三个 Repos 深度研究

### Agent-R1 (arxiv 2511.14460)
- 基于 veRL，支持 PPO/GRPO/REINFORCE++
- **核心创新：Action Mask** — binary mask 区分 model-generated tokens (mask=1) vs tool response tokens (mask=0)。防止 RL 试图 "学习" 环境返回的内容（stdout/stderr）。
- **但 process rewards 是死代码**（注释掉了）。实际只用 outcome reward = `-1 + format_score + answer_score`
- **结论：Action Mask 概念有意思，但 SkyRL/veRL 已经有类似机制。实际可借鉴不多。**

### ToolRL (arxiv 2504.13958)
- Decomposed reward: `R = R_format(0/1) + R_correct(tool_name × Jaccard + param_name × Jaccard + param_value × exact)`
- Dynamic scaling: format reward 先高后低，correctness 先低后高（150 steps 平滑过渡）
- **关键限制：单轮 only + 不执行 tool（对比 gold label）。** 名字 misleading — 更像 "keyword matching RL"
- Length reward 反而伤害 tool use（46% → 33%）。GRPO cold-start > SFT-then-RL。
- **结论：decomposed reward 思路可记住，但场景跟我们太不一样（单轮 vs 多轮、gold label vs 真实执行）。**

### VerlTool (arxiv 2509.01055) ⭐ 最有用
- **Tool abandonment 是真实问题** — 不加激励，agent 会自发停止使用 tools（rate 掉到 30% 以下）
- **Group-level curiosity penalty（最佳方案）:** `bonus = 0.5 × I(used_tool) × max(0, 0.3 - group_rate)` — 自适应，tool use 越少 bonus 越大
- 支持 bash + MCP + 独立 tool server（HTTP service 执行 tool calls）
- Tool server 架构 = 我们的 Harbor Docker sandbox 架构（独立容器执行 bash，HTTP 返回结果）
- **结论：直接可用。Group-level curiosity penalty + tool server 架构都跟我们的 setup 对齐。**

### 三个 Repo 总结

| Repo | 借鉴什么 | 有用程度 |
|------|---------|---------|
| Agent-R1 | Action Mask（SkyRL 已有） | ⭐ 低 |
| ToolRL | Decomposed reward 思路 | ⭐⭐ 中（思路好，场景不同） |
| VerlTool | Curiosity penalty + tool server | ⭐⭐⭐ 高（直接可用） |

Knowledge files: `submodules/Agent-R1/knowledge.md`, `submodules/ToolRL/knowledge.md`, `submodules/verl-tool/knowledge.md`

---

## 对话 7: 我们的差异化价值

### VerlTool 有 infra，我们有 environment design

VerlTool 的 tasks 都是 single-skill（GSM8K 用 Python 算、HotpotQA 用 search 查）。

**我们做的不一样的东西：**

1. **Professional domain tasks** — law, finance, medical, consulting。真实专业任务，不是 toy benchmarks。
2. **Multi-tool composition** — 每个 task 天然需要组合多种工具（读 PDF + 写 script + 分析 + 写报告）。
3. **Building-block environment 四原则** — 提供积木、告诉对不对、不告诉怎么搭、不告诉积木在哪。VerlTool 没有这层设计。
4. **Task families for generalization** — 跨 domain analogical reasoning。VerlTool 每个 domain 单独训。

**VerlTool = 好车（训练引擎）。我们 = 新赛道（professional task environment）。**

我们的 contribution：
- 用 VerlTool/SkyRL 的训练引擎（包括 curiosity penalty）
- 在 professional task environment 上训练
- 证明：bash agent + process signals + professional tasks = agents that compose tools across domains

---

## Plan 状态

Plan file: `~/.claude/plans/polymorphic-honking-kay.md`

6 个步骤：
1. Download all APEX file attachments
2. Convert training tasks (100) to Harbor format
3. Convert ALL eval tasks (480, including 175 with file attachments) to Harbor format
4. Local verification
5. Push to HF + SkyRL training config
6. Re-run baseline eval in Harbor

**研究阶段完成。** 主要参考：VerlTool（curiosity bonus + tool server 架构）。

---

## 对话 8: Tool Composition 怎么 Measure？

### 核心问题

去掉了 hardcoded tools 后，process signals 里的 tool composition 和 tool creation 怎么验证？

### 三个方向都不好

1. **检测行为 pattern**（agent 命令里出现 2+ 文件名）— 读了不同文件 ≠ 用了不同 tool
2. **检测 output 质量**（cross-reference keywords）— keyword matching is the worst
3. **在 task design 里强制**（task 需要 multi-file 才能答对）— multi-file composition ≠ multi-tool composition

### Lily 的 Insight：两层能力

**Layer 1: Multi-step workflow（task 内的 composition）**
- pdftotext → grep → python → cat report
- 把简单工具组合成解决方案
- APEX 单个 task 可以验证 — correctness reward 自然驱动

**Layer 2: Workflow reuse（across tasks）**
- 学会了一套 workflow 后，能不能复用到更复杂的任务？
- 跟 hand-draw 一样：同 domain 内从 diamond → cappuccino

### 关键决策：Within-domain > Cross-domain

**Cross-domain reuse（横向）** = generalization / 学术方向，离 industry 远
**Within-domain complexity scaling（纵向）** = industry 方向 ⭐

- 先选一个 domain 深挖（IB — heavy tool usage）
- 从简单 financial analysis → 复杂 multi-scenario LBO
- 这才是 industry care 的："agent 能不能真正做好 IB 的工作"

### Reward 简化决策

先不强行 measure composition。用更简单的 reward：
- Correctness（答对了）
- Tool engagement（用了 bash tool，不是纯说话）
- Curiosity bonus（防 abandonment）

如果 task 本身需要 composition 才能答对，agent 会自发学会。观察训练行为再决定是否加 process signals。

---

## 对话 9: Finance/IB Domain Difficulty 分析

### Training Set: 25 Finance Tasks

| Tier | Count | 占比 | 特征 |
|------|-------|------|------|
| Easy | 2 | 8% | CSV filtering, 基础 EV bridge |
| Medium | 6 | 24% | 单领域分析（DCF, bond pricing, mortgage） |
| Hard | 17 | 68% | 多步建模，10-36 个 sub-questions |

**严重偏 Hard** — 68% 是 Hard。只有 2 个 Easy。

### 涵盖的 IB 技能树

LBO, DCF, M&A, restructuring, securitization, fixed income, real estate PE, regulatory — 核心 IB 技能基本都有。

### 推荐 Curriculum（4 tiers）

1. **Tier 1 (warm-up)**: 2 tasks — 简单数据提取
2. **Tier 2 (foundation)**: 6 tasks — 单领域 financial analysis
3. **Tier 3 (integration)**: 8 tasks — 多步建模，7-13 criteria
4. **Tier 4 (mastery)**: 9 tasks — 复杂多技能，10-36 sub-questions

### Eval Set: 160 IB Tasks

相反分布 — 54% Easy, 31% Medium, 15% Hard。Train hard → eval easy 可能效果不错。

### 问题

Tier 1 太薄（只有 2 tasks）。可能需要补充简单 tasks 或者从 eval set 的简单 tasks 借用。

---

## 对话 10: Difficulty Distribution + Next Steps

### 问题：Training set 严重偏 Hard

Finance 25 tasks: Easy 2 (8%), Medium 6 (24%), Hard 17 (68%)

### 决策：先跑起来，不行再加 curriculum

- Option 1 ✅ **直接训，不管 difficulty 分布**。Train hard, eval easy 可能反而是好事。
- Option 2（备选）：用其他 domain 的 Easy tasks 补充 warm-up
- Option 3（备选）：自己简化 Hard tasks 生成 Easy 版本

**如果 pipeline 跑起来后 reward 太低（agent 学不动），再做 curriculum learning 用 Easy tasks 过渡。**

---

## 当前状态

- Plan: `~/.claude/plans/polymorphic-honking-kay.md`（已更新）
- 研究完成，方向明确
- **执行中：**
- ✅ Step 1: Download all APEX data (training 132 PDFs + eval 33 world zips / 8.9GB)
- ✅ Step 2: Convert 100 training tasks to Harbor format (100/100 OK)
- ✅ Step 3: Verification (100/100 structure OK, 176 files, 1140 criteria)
- ✅ Step 4: SkyRL training config (harbor_trial_config.yaml + run_apex_train.sh)
- ✅ Step 5: Push to HF
  - `lilyzhng/apex-harbor-train` (100 tasks) ✅
  - `lilyzhng/apex-harbor-eval` (480 tasks, 18GB) ✅
- ✅ Step 6: Convert 480 eval tasks (446/480 with files, 93%)
- ✅ Smoke test: `harbor run -p tasks/apex-finance-1588/ -a oracle` — pipeline works end-to-end
- ✅ Reward scorer simplified (removed old process signals, kept correctness + tool_engaged)
- ✅ Re-tested with Claude Sonnet: reward 0.5 (5/10 criteria)

---

## 对话 11: Repo Study Q&A

### Agent vs Environment Tokens
- Action Mask 区分 model tokens vs env tokens，防止 RL 学习 stdout 内容
- SkyRL 已经处理了这个，不需要我们操心

### ToolRL 名字 misleading
- 不执行 tool，只对比 gold label — 更像 "keyword matching RL"
- Dynamic scaling = 训练过程中调整 reward 权重（format 先高后低，correctness 先低后高，150 steps 平滑过渡）

### VerlTool Tool Server
- Tool server = 独立 HTTP service 执行 tool calls，跟 training 隔离
- 类比：厨房（tool server）跟办公室（GPU training）分开
- **Harbor 就是这个架构** — Docker container 执行 bash，HTTP 返回结果

### 我们跟 VerlTool 的区别
- VerlTool 有 infra（怎么训），我们有 environment design（训什么）
- VerlTool tasks = single-skill（GSM8K, HotpotQA）
- 我们 = professional domain tasks + multi-tool composition + building-block 四原则 + task families
- **VerlTool = 好车。我们 = 新赛道。**

---

## 对话 12: 方法论定位

Lily 明确：**不在乎 algorithm novelty，在乎方法是否正确 + 能否在 industry-relevant domains 上做出结果。**

用已验证的方法（VerlTool curiosity bonus + SkyRL + Harbor），在真正有价值的 domain 上做。

---

## 对话 13: License + Within-Domain Strategy

### License 确认
- `mercor/apex-agents` (480) = eval only, 不能训练
- `mercor/APEX-v1-extended` (100) = CC-BY-4.0, 可以训练
- 不碰灰色地带，v1-extended 做 training，apex-agents 只做 eval

### Within-domain > Cross-domain
- Cross-domain（law → consulting → IB）= generalization / 学术方向，离 industry 远
- **Within-domain complexity scaling** = industry 方向 ⭐
  - 在 IB domain 里从简单 → 复杂
  - 跟 hand-draw 一样的模式：同 domain，diamond → cappuccino
  - 这才是 industry care 的

---

## 对话 14: Smoke Test + Reward 修正

### Harbor CLI Smoke Test
- `harbor run -p tasks/apex-finance-1588/ -a oracle` → pipeline 端到端跑通
- `harbor run -p tasks/apex-finance-1588/ -a terminus-2 -m openrouter/anthropic/claude-sonnet-4` → Claude Sonnet 拿了 0.5（5/10 criteria）

### Reward 修正（重要教训）
**问题：** reward_scorer.py 用了旧的 process signals（tool_use 0.1, composition 0.15, creation 0.15），但我们在对话 8 已经决定简化为 correctness + tool engagement + curiosity bonus。

**原因：** 写代码时没有 re-read brainstorm doc，直接 copy 了旧的 reward.py 的 pattern。

**修正：**
- 去掉了所有 process signals
- 简化为：correctness = criteria_met / criteria_total，gated by file existence
- tool_engaged = boolean flag（有没有创建 output）
- Curiosity bonus 在 SkyRL 层加，不在 test.sh 里

**教训记录到 CLAUDE.md：** 执行前必须 re-read brainstorm doc。Brainstorm doc 是 source of truth，不是旧代码。

---

## 当前状态 (2026-03-22 05:30)

**Pipeline 完成，验证通过。等待 GPU 训练。**

### 完成的工作
- ✅ 所有数据下载（training 132 PDFs + eval 33 world zips / 8.9GB）
- ✅ 100 training tasks 转 Harbor format
- ✅ 480 eval tasks 转 Harbor format（446/480 有 files）
- ✅ Push 到 HF: `lilyzhng/apex-harbor-train`, `lilyzhng/apex-harbor-eval`
- ✅ SkyRL training config: `harbor_trial_config.yaml` + `run_apex_train.sh`
- ✅ Smoke test: Harbor CLI + Claude Sonnet → reward 0.5 (5/10 criteria)
- ✅ Reward scorer 简化为 correctness + tool_engaged

### 代码位置
All in `claude/builder/`:
- `scripts/download_apex_files.py`
- `scripts/convert_apex_to_harbor.py` + `scripts/convert_apex_eval.py`
- `scripts/harbor_template/` (Dockerfile, test.sh, reward_scorer.py)
- `scripts/harbor_trial_config.yaml`
- `scripts/run_apex_train.sh`
- `scripts/verify_harbor_tasks.py`

### 下一步
- 在 GPU 机器上跑 SkyRL training（需要 4x A100 or similar）
- 实现 curiosity bonus 在 SkyRL training loop 里
- 训练后在 480 eval tasks 上跑 baseline comparison
