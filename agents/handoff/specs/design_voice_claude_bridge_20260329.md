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

### How It Works

1. GPT Realtime handles normal conversation at low latency (~500ms)
2. When the user asks something that needs deeper capability, GPT calls `use_cli`
3. The voice service spawns `claude --print` as a child process with the user's request
4. The CLI launches from `agents/genius-product/` as its working directory, so it inherits Jackie's CLAUDE.md, skills, and project context automatically
5. Claude Code runs with full access: bash, MCP, skills, files, everything
6. The result (text) is returned to GPT Realtime
7. GPT speaks the answer back to the user

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
async function useCli(task: string): Promise<string> {
  const { execFileSync } = require("child_process");
  try {
    const result = execFileSync(
      "claude",
      ["--print", "--max-turns", "5", task],
      {
        timeout: 60_000,
        encoding: "utf-8",
        cwd: "/home/node/SofaGenius/agents/genius-product",  // Inherits Jackie's CLAUDE.md + context
        env: {
          ...process.env,
          CLAUDE_CODE_ENTRYPOINT: "voice-bridge",
          CLAUDE_MODEL: process.env.CLAUDE_BRIDGE_MODEL || "claude-haiku-4-5-20251001"
        }
      }
    );
    // Trim to reasonable size for GPT to speak
    return result.slice(0, 3000);
  } catch (err: any) {
    return `Failed to complete task: ${err.message?.slice(0, 500)}`;
  }
}
```

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
| **use_cli bridge (proposed)** | One tool gives access to everything on the machine. No maintenance per capability. | 5-30s latency for complex tasks. Extra cost (Claude API call). |
| **Keep hardcoding tools** | Fast, predictable latency. | Doesn't scale. Every new capability = code + deploy. Phone Jackie stays limited. |
| **Replace GPT Realtime with Claude** | Single model, no bridge needed. | Claude doesn't have a realtime voice API. Would need STT + TTS pipeline = higher latency, more complexity. |
| **MCP client in voice service** | Direct access to MCP servers. | Have to implement MCP client protocol in TypeScript. Each server still needs explicit wiring. Doesn't get bash/skills. |
| **Gemini Live API** | Potentially cheaper. Also supports function calling. | Same fundamental problem: tools are still hardcoded. Switching models doesn't solve the capability gap. But worth exploring separately for cost. |

---

## Scope

### v1 (next PR)
- [ ] Add `use_cli` tool definition to `tools.ts`
- [ ] Implement `useCli()` function using `claude --print` with `execFileSync` (no shell injection)
- [ ] Update system prompt to instruct GPT when to use `use_cli` vs built-in tools
- [ ] Add timeout handling (60s max, graceful error message)
- [ ] Test with common scenarios: PR status, deployment checks, file lookups

### v1.1 (follow-up)
- [ ] Streaming: Instead of waiting for full Claude response, stream partial results back so GPT can start speaking sooner
- [ ] Context passing: Include recent conversation transcript in the `use_cli` prompt so Claude has context
- [ ] Cost tracking: Log Claude API usage from voice bridge calls separately

### Future considerations
- Gemini Live API as alternative voice model (separate investigation, orthogonal to this bridge)
- Persistent Claude Code session instead of one-shot `--print` calls (lower latency for sequential tasks)
- Two-way bridge: Claude Code can trigger voice responses (proactive notifications via call)

---

## Risks

**Latency perception.** 5-30 second pauses could feel broken. Mitigation: GPT says "checking on that" before calling. The system prompt enforces this.

**Cost stacking.** Each `use_cli` call costs both OpenAI (GPT Realtime) and Anthropic (Claude API) tokens. Mitigation: Built-in tools remain the fast path for common operations. `use_cli` is the fallback, not the default.

**Prompt injection via voice.** User's spoken words become a prompt to Claude Code. Mitigation: Claude Code already has safety guardrails. The `--max-turns 5` flag limits runaway execution.

**Output length.** Claude might return a 10-page analysis that GPT tries to read aloud. Mitigation: Truncate to 3000 chars. System prompt instructs Claude to be concise.

---

## Open Questions

1. **~~Should `use_cli` have access to Jackie's private memory repo?~~** Resolved: by setting `cwd` to `agents/genius-product/`, the CLI inherits Jackie's CLAUDE.md which contains memory paths and project context. For private memory access, the CLAUDE.md can reference `JACKIE_MEMORY_DIR`.
2. **Rate limiting?** Should we limit how many `use_cli` calls per session to prevent cost runaway?
3. **Which Claude model?** Default to Haiku 4.5 for speed (most bridge calls are lookups/summaries). Configurable via `CLAUDE_BRIDGE_MODEL` env var to swap to Sonnet/Opus without redeploying.
