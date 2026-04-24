---
date: 2026-03-30
time: 10:30
---
# Voice + Claude Code Bridge - Design Doc

> Date: 2026-03-29
> Owner: Lily (CEO, review) | Jackie (product + voice) | Bill (build + design)
> Status: Draft
> Context: Phone Jackie runs GPT Realtime for voice but has only hardcoded tools. Discord Jackie runs Claude Code with full capabilities. They're on the same machine but completely separate. This design bridges them.

---

## First Principles Check

1. **Who is this for?** Lily. She calls Phone Jackie and expects the same capabilities as Discord Jackie.
2. **What problem are we actually solving?** Phone Jackie is "dumb" compared to Discord Jackie. Every new capability requires hardcoding a tool, deploying, and restarting. Meanwhile Discord Jackie can improvise with bash, MCP servers, skills, file access, git, web search, etc.
3. **Does the delivery model meet her where she already is?** Yes. She's already calling Jackie. This makes those calls more capable without changing anything about how she uses them.
4. **What's the simplest version that tests whether this works?** One new tool in `tools.ts` that shells out to `claude` CLI. Phone Jackie calls it when built-in tools aren't enough.
5. **Why this approach over alternatives?** See alternatives section below. The key insight: Claude Code already has the full toolkit. We just need to let the voice service call it instead of rebuilding everything from scratch.

---

## Problem

Phone Jackie's voice service is a thin WebSocket bridge:

```
Phone -> Twilio -> Voice Service (Fastify) <-> OpenAI Realtime API (GPT)
                                                    |
                                              Tool calls (14 hardcoded)
```

GPT Realtime provides speech-to-speech and function calling. But the functions are limited to what we manually define in `tools.ts`. Today that's 14 tools: memory ops, time, web search, calendar, email, and a generic skill bridge.

Discord Jackie runs inside Claude Code, which has:
- Bash (run any command)
- MCP servers (Discord, Gmail, etc.)
- Skills (dozens of specialized capabilities)
- File system access
- Git operations
- Web search/fetch
- Tool composition (chain tools dynamically)

The gap is huge. Phone Jackie can't look up a PR, check deployment status, run a script, use any MCP server, or do anything we haven't explicitly coded. Discord Jackie can do all of this and more.

---

## Proposed Solution

Add a single `use_cli` tool to the voice service that delegates complex requests to the Claude Code CLI running on the same machine.

### Architecture

```
Phone -> Twilio -> GPT Realtime (fast voice brain, handles conversation)
                        |
                   Tool calls
                        |
            +-----------+-----------+
            |                       |
     Built-in tools           use_cli tool
     (fast path)              (full capability)
     - memory ops             - shells out to `claude` CLI
     - time                   - returns text result
     - web search             - GPT speaks the answer
     - calendar/email
```

### What Is the CLI Session?

When a phone call starts, the voice service spawns a `claude` CLI subprocess. Think of it as a **Jackie clone agent** that lives for the duration of the call. It's not Discord Jackie. It's a fresh, separate Claude Code session running on the same agent computer.

**What it has access to:**
- **Jackie's identity.** Launches from `agents/genius-product/`, so it reads Jackie's CLAUDE.md (personality, instructions, memory paths)
- **Jackie's env vars.** The voice service inherits Jackie's `.env` at startup (`launch-bg.sh` sources it). The CLI subprocess inherits `process.env`, so it has `GH_TOKEN` (can push to GitHub), `TAVILY_API_KEY` (web search), and all other tokens
- **Jackie's private memory.** Can read/write `jackie-memory/` (call logs, action items, context notes) since it's on the same machine
- **Full CLI toolkit.** Bash, git, file system, Python scripts, any command-line tool installed on the machine
- **No Discord.** The CLI does NOT have the Discord MCP plugin. It can't read or reply to Discord messages. That's Discord Jackie's domain.

**What it does NOT have:**
- No connection to the phone call audio. It only receives text tasks and returns text results.
- No awareness of the ongoing conversation unless GPT passes context in the task description.

### How It Works

**Session lifecycle (one CLI per phone call):**
1. When a phone call connects, the voice service spawns a persistent `claude` CLI subprocess
2. The CLI session stays alive for the entire call, maintaining conversation context across multiple `use_cli` calls
3. When the call ends, the CLI subprocess is killed

**Per-tool-call flow:**
1. GPT Realtime handles normal conversation at low latency (~500ms)
2. When Lily asks something that needs deeper capability, GPT calls `use_cli`
3. The voice service sends the task to the already-running CLI session via stdin
4. The CLI executes the task. It remembers what it did earlier in this call.
5. The result (text) is returned to GPT Realtime
6. GPT (as Jackie) speaks the answer back to Lily

**Why persistent vs ephemeral:** First call has cold start (~3-5s for CLAUDE.md loading), but subsequent calls are faster since the session is already warm. The CLI also remembers context across calls (e.g., "check PR #117" then "what were the comments on it?"), which ephemeral sessions can't do.

### Example: "Document our conversation and push to GitHub"

1. Lily says on the phone: "Document our conversation and push it to GitHub"
2. GPT Realtime calls `use_cli({task: "Write a summary of today's phone call with Lily. Save it to jackie-memory/calls/ with today's date. Then git add, commit, and push to GitHub."})`
3. The CLI session (Jackie clone) executes:
   - Writes a call summary to `jackie-memory/calls/2026-03-29.md`
   - Runs `git add .`, `git commit -m "Call summary 2026-03-29"`, `git push`
   - Returns "Done. Call summary saved and pushed to GitHub."
4. GPT speaks: "Done, I've saved the summary and pushed it."

This works because the CLI has `GH_TOKEN` from Jackie's `.env` and write access to `jackie-memory/`.

### Tool Routing

GPT Realtime decides which tool to call based on the tool descriptions in the system prompt. The routing principle is simple: **use built-in tools for speed, fall back to `use_cli` for everything else.**

| User says | Route | Why |
|-----------|-------|-----|
| "What time is it?" | `get_current_time` | Exact match, <1s |
| "Save a note about this idea" | `save_memory` | Exact match, <1s |
| "Search for latest AI news" | `web_search` | Exact match, <1s |
| "What's on my calendar?" | `check_calendar` | Exact match, <1s |
| "Check my email" | `check_email` | Exact match, <1s |
| "What's the status of PR #117?" | `use_cli` | No built-in PR tool |
| "Document our call and push to GitHub" | `use_cli` | Multi-step: write file + git commit + push |
| "Deploy the latest changes" | `use_cli` | No built-in deploy tool |
| "How many open issues do we have?" | `use_cli` | Needs `gh` CLI |
| "Read me the last 3 commits" | `use_cli` | Needs `git log` |
| "Check if the voice service is running" | `use_cli` | Needs `lsof` / process check |

**How this is enforced:** The system prompt tells GPT: "You have fast built-in tools for common tasks. For anything beyond those, use `use_cli`. Before calling `use_cli`, tell Lily you're looking into it so she knows to expect a short pause."

The `use_cli` tool description itself reinforces this: "Use this when the user asks for something beyond your built-in tools: checking PRs, running scripts, deployment status, complex research, file operations, or anything you can't do with your other tools."

**Edge cases:** If a task could go either way (e.g., "search the web for X and summarize it"), GPT may use `web_search` (fast) or `use_cli` (richer summary). This is fine. The built-in tools are a performance optimization, not a hard boundary. If GPT routes something to `use_cli` that could have used a built-in tool, the result is slower but still correct.

### Tool Definition

```typescript
{
  type: "function",
  name: "use_cli",
  description: "Run a task using the Claude Code CLI, which has full access to bash, files, git, MCP servers, and all agent skills on this machine. Use this when the user asks for something beyond your built-in tools: checking PRs, running scripts, deployment status, complex research, file operations, or anything you can't do with your other tools. This is slower (5-30s) so tell the user you're looking into it before calling.",
  parameters: {
    type: "object",
    properties: {
      task: {
        type: "string",
        description: "Natural language description of what to do. Be specific about what information to return."
      }
    },
    required: ["task"]
  }
}
```

### Implementation

```typescript
import { spawn, ChildProcess } from "child_process";

let cliProcess: ChildProcess | null = null;

/** Start a persistent CLI session when the call begins */
function startCliSession(): void {
  cliProcess = spawn("claude", ["--json", "--max-turns", "5"], {
    cwd: "/home/node/SofaGenius/agents/genius-product",
    env: {
      ...process.env,
      CLAUDE_CODE_ENTRYPOINT: "voice-bridge",
      CLAUDE_MODEL: process.env.CLAUDE_BRIDGE_MODEL || "claude-haiku-4-5-20251001"
    },
    stdio: ["pipe", "pipe", "pipe"]
  });
}

/** Send a task to the persistent CLI session */
async function useCli(task: string): Promise<string> {
  if (!cliProcess) startCliSession();
  // Send task via stdin, read result from stdout
  // (exact protocol depends on claude --json streaming format)
  cliProcess.stdin.write(task + "\n");
  const result = await readNextResponse(cliProcess.stdout);
  return result.slice(0, 3000);
}

/** Kill the CLI session when the call ends */
function endCliSession(): void {
  if (cliProcess) {
    cliProcess.kill();
    cliProcess = null;
  }
}
```

Note: The exact stdin/stdout protocol needs to be validated against `claude --json` streaming format. The key design decision is one persistent process per call, not one per tool invocation.

### UX Flow

**Fast path (existing tools, <1s):**
> "Jackie, what time is it?" -> `get_current_time` -> "It's 8:35 PM Pacific."

**CLI bridge (new, 5-30s):**
> "Jackie, what's the status of our latest PR?"
> Jackie: "Let me check that for you."
> `use_cli("Check the latest PR on the SofaGenius repo. Get the PR number, title, status, and any review comments.")`
> Jackie: "PR #116 is open, it's the voice service fixes. No reviews yet."

The key UX detail: GPT should say something like "give me a sec" or "let me look into that" BEFORE calling `use_cli`. The system prompt instructs this. The pause feels natural because humans expect a delay when someone is looking something up.

---

## Alternatives Considered

| Approach | Pros | Cons |
|----------|------|------|
| **use_cli bridge (proposed)** | One tool gives access to everything on the machine. No maintenance per capability. CLI runs under Anthropic subscription (no extra API cost). | 5-30s latency for complex tasks. |
| **Keep hardcoding tools** | Fast, predictable latency. | Doesn't scale. Every new capability = code + deploy. Phone Jackie stays limited. |
| **Replace GPT Realtime with Claude** | Single model, no bridge needed. | Claude doesn't have a realtime voice API. Would need STT + TTS pipeline = higher latency, more complexity. |
| **MCP client in voice service** | Direct access to MCP servers. | Have to implement MCP client protocol in TypeScript. Each server still needs explicit wiring. Doesn't get bash/skills. |
| **Gemini Live API** | Potentially cheaper. Also supports function calling. | Same fundamental problem: tools are still hardcoded. Switching models doesn't solve the capability gap. But worth exploring separately for cost. |

---

## Scope

### v1 (next PR)
- [ ] Add `use_cli` tool definition to `tools.ts`
- [ ] Implement persistent CLI session: spawn on call start, reuse across tool calls, kill on call end
- [ ] Validate `claude --json` stdin/stdout protocol for sending tasks and reading results
- [ ] Update system prompt to instruct GPT when to use `use_cli` vs built-in tools
- [ ] Add timeout handling (60s per task, graceful error message)
- [ ] Test with common scenarios: PR status, deployment checks, file lookups, multi-step queries

### v1.1 (follow-up)
- [ ] Streaming: Instead of waiting for full Claude response, stream partial results back so GPT can start speaking sooner
- [ ] Cost tracking: Log Claude API usage from voice bridge calls separately
- [ ] Graceful reconnect: If the CLI process crashes mid-call, restart it transparently

### Future considerations
- Gemini Live API as alternative voice model (separate investigation, orthogonal to this bridge)
- Two-way bridge: Claude Code can trigger voice responses (proactive notifications via call)

---

## Risks

**Latency perception.** 5-30 second pauses could feel broken. Mitigation: GPT says "checking on that" before calling. The system prompt enforces this.

**Cost stacking.** GPT Realtime charges per audio token (OpenAI billing). The Claude Code CLI runs on agent computer under the Anthropic subscription, so no additional per-call API cost. The main cost concern is OpenAI: longer calls with more back-and-forth = more audio tokens. Mitigation: Built-in tools remain the fast path for common operations. `use_cli` is the fallback, not the default.

**Prompt injection via voice.** User's spoken words become a prompt to Claude Code. Mitigation: Claude Code already has safety guardrails. The `--max-turns 5` flag limits runaway execution.

**Output length.** Claude might return a 10-page analysis that GPT tries to read aloud. Mitigation: Truncate to 3000 chars. System prompt instructs Claude to be concise.

---

## Open Questions

1. **~~Should `use_cli` have access to Jackie's private memory repo?~~** Resolved: by setting `cwd` to `agents/genius-product/`, the CLI inherits Jackie's CLAUDE.md which contains memory paths and project context. For private memory access, the CLAUDE.md can reference `JACKIE_MEMORY_DIR`.
2. **Rate limiting?** Should we limit how many `use_cli` calls per session to prevent cost runaway?
3. **Which Claude model?** Default to Haiku 4.5 for speed (most bridge calls are lookups/summaries). Configurable via `CLAUDE_BRIDGE_MODEL` env var to swap to Sonnet/Opus without redeploying.
