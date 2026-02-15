# Sofa Genius — Phase 1 Wrap-Up

## Done
- Full-stack app: FastAPI backend + Vite/React/TypeScript frontend
- Anthropic tool_use agent loop with SSE streaming
- 4 W&B tools: get_wandb_info, list_wandb_runs, get_run_metrics, analyze_run_health
- 7 anomaly detectors: spike, divergence, oscillation, grad explosion, overfitting, plateau, NaN
- Auto-discovery of W&B entity (username) and metric keys from run history
- Two-panel UI: chat (left) + Health Card with Recharts plots (right)
- Markdown rendering in chat, conversation history for multi-turn
- New Chat button, custom user avatar, design system (cream/gold/stone palette)

## Remaining (Non-Urgent)
- Action buttons on Health Card are visual-only (no onClick handlers)
- No persistent chat history (refreshing the page clears everything)
- No loading skeleton for the Health Card while tool executes
- Example queries in empty state are hardcoded, could adapt to user's projects

## Known Bugs
- Claude occasionally still leaks partial JSON into chat text despite regex stripping
- If W&B API key is invalid/missing, error message is generic ("something went wrong")
- Conversation history grows unbounded — no truncation for long sessions, may hit token limits

## Improvements for Phase 2+
- Stream token-by-token instead of waiting for full text block (true SSE streaming with Anthropic SDK)
- Add Phase 2 tools: SQL/data analyst, HF Scout, Modal job launcher
- Voice mode (Pipecat / Web Speech API)
- Task Runner stepper UI (Proposed → Approved → Executed)
- Rate limiting / caching for W&B API calls
- Evaluate Hashbrown or similar for dynamic AI-generated UI components
