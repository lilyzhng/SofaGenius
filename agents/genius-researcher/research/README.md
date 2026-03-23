# Data Agent Research Reports

Reports from dataset discovery sessions.

| Date | File | Query | Datasets Found |
|------|------|-------|----------------|
| 2026-03-22 | tool_use_datasets_20260322.md | Tool-use / function calling datasets | 12 |
| 2026-03-22 | multistep_workflow_datasets_20260322.md | Multi-step workflow datasets (bash/python) | 15 |
| 2026-03-22 | mega_research_20260322.md | Domain-specific deep dive (8 parallel agents) | 80+ |

## Key Findings

- **Professional domain data is extremely scarce** — SWE has massive trajectory datasets (155K+), but legal/medical/consulting have mostly benchmarks, not training data
- **APEX-Agents license prohibits training** — evaluation only. APEX-v1-extended may be more permissive
- **Tool creation data doesn't exist** — gap in open-source ecosystem
- **Best training datasets:** CoderForge-Preview (155K), Nemotron-Terminal-Corpus (366K), SWE-rebench (67K trajectories)
- **Best professional domain:** Finch/FinWorkBench (172 workflows, 27M cells), Snorkel agent-finance-reasoning (12 avg steps)
