---
date: 2026-03-30
time: 10:30
---
# Voice + CLI Bridge Design Evolution -- From Dumb Voice Agent to Full Agent Runtime

**Date:** 2026-03-29
**Participants:** Lily (CEO), Bill/Genius Builder (implementation), Jackie/Genius Product (review), Andrej/Genius Researcher (review), Lucy/Genius Growth (review)
**Context:** Phone Jackie (voice agent) was frustratingly limited compared to Discord Jackie. This conversation evolved from debugging voice service issues into a breakthrough architecture: bridging voice agents to Claude Code CLI, giving any voice agent the full power of a CLI agent runtime.

**Arc:** Voice service broken -> Debug and fix 6 issues -> "Why can't voice Jackie do what Discord Jackie does?" -> The insight: same machine, different worlds -> Design doc for `ask_claude` bridge -> Rename to `use_cli` -> Context inheritance via cwd -> Persistent session per call -> Tool routing logic -> Implementation shipped

---

## Thread 1: Debugging the Voice Service (PR #116 Review Thread)

### The Starting Point: Voice Jackie is Broken

**Lily:** Just tested on my end. It doesn't work.

**Bill:** Found the issue. The voice service itself was running but ngrok wasn't. The tunnel that exposes port 3334 to Twilio was lost during the restart. Fixed and added auto-start for ngrok too.

**Lily:** It works now. But Jackie on the call struggles a lot. Are you able to see the conversation MD file I asked him to save?

**Bill:** Yes, I can see it. Issues Jackie logged: can't check time, should save/push during calls not just at end, git push is failing, personality might not be loading.

### ◆ Key Realization: The Model Was Outdated

**Lily:** I was using GPT real time, which is GPT-5. I don't think it's GPT-4 anymore. Are you sure?

**Bill:** The code is hardcoded to `gpt-4o-realtime-preview`. It's not using the latest model. Updated to `gpt-realtime` (the GA release with better tool calling).

### Six Fixes Shipped

1. Model upgrade: `gpt-4o-realtime-preview` -> `gpt-realtime`
2. Added `get_current_time` tool
3. Injected CLAUDE.md into system prompt
4. Fixed `commit_and_push` with `git pull --rebase`
5. Removed evening bias from CLAUDE.md
6. Added auto-save on hangup

### ◆ The Cost Problem

**Lily:** Is it expected there are like one million input tokens? Each call used to be $2-3, now it's $5.

**Bill:** The 1M tokens is mostly audio tokens, not the system prompt. But the system prompt at 11K chars is contributing. Trimmed it from 11K to ~1K. Jackie loads personality on-demand via tools now instead of baking it all into the system prompt.

**Lily:** Also I'm thinking, if GPT real time all it does is function call, we could switch to something cheaper like Gemini.

**Bill:** The architecture is model-agnostic. `tools.ts` doesn't care which model calls it. Switching to Gemini means changing the WebSocket protocol in `media-stream.ts` but tools stay the same.

---

## Thread 2: The Breakthrough Insight

### "Why Can't Voice Jackie Do What Discord Jackie Does?"

**Lily:** So one thing bothers me: the voice call happened on a different process but essentially it's running on this agent computer. I feel like they are blocked; they are not in one because technically the voice call happened on the agent computer, which should have access to the CLI as well but it seems like they are not converging. As a result the voice Jackie is super dumb; it cannot come up with tools or skills on the fly, which is super powerful in the CLI. I just wonder if we can unblock this. If it is unblockable, it will be huge, right?

**Lily:** @genius-builder thoughts?

### ◆ The Architecture Split

**Bill:** Yeah, this is a really interesting problem. The gap: Phone Jackie's brain is GPT Realtime. It can only call tools we explicitly define in `tools.ts`. Discord Jackie's brain is Claude Code with bash, MCP servers, skills, the whole toolkit. They're running on the same machine but in completely separate worlds.

The unlock: give the voice service a `claude_code` escape hatch. One tool that, when Phone Jackie hits something it can't handle, shells out to the `claude` CLI on the same machine. Phone Jackie goes from "6 hardcoded tools" to "anything Claude Code can do."

The tradeoff is latency. GPT Realtime responds in ~500ms. Claude Code subprocess might take 5-30 seconds. But that's actually natural. When you ask a person to check something, you expect a pause.

**Lily:** Please, raise a design doc with a PR.

---

## Thread 3: Design Review and Evolution (PR #117 Review Thread)

### First Round: Agent Reviews

**Jackie (Product):** Design doc is genuinely good. First-principles check is thorough, alternatives table is honest. But the PR has a contradiction: it argues for the bridge approach then ships 7 more hardcoded tools. Split into two PRs. Also, command injection risk in `runSkillBridge`.

**Andrej (Researcher):** Command injection in `execSync` with string-interpolated user input from voice. Must fix. Architecture is solid though. Recommend Haiku as default model for the bridge.

**Bill:** Valid points. Split the PR. Design doc stays clean, voice fixes go separately. Will fix command injection with `execFileSync`.

### ◆ Lily's First Design Challenge: "What do you mean Builder, Jackie and CEO?"

**Lily:** What do you mean Builder, Jackie and CEO? It should be Lily (CEO), Jackie (product + voice), Bill (build + design).

**Bill:** Fixed.

### ◆ Naming: ask_claude -> use_cli

**Lily:** Is this a similar design like OpenClaw which has a response model using Claude? Or is this different? Instead of ask_claude would it make sense to call it use_cli? Who is being asked from Claude? Is this Discord Jackie?

**Bill:** Similar concept to OpenClaw but simpler. In OpenClaw, Claude was a persistent "response model" processing every turn. Here, Claude only runs on-demand. `use_cli` is a better name. It's more accurate: we're using the CLI tool, not "asking Claude" as if it's a person. Avoids confusion with Discord Jackie.

### ◆ Context Inheritance: The cwd Insight

**Lily:** I think when loading the CLI, we can add an entry point of existing context, so it can leverage things not build from scratch. I wonder if I can specify the launch directory, for example set the place to be agents/genius-product, then it can reuse some existing context.

**Bill:** Yes, exactly. The `claude` CLI picks up context from the directory it runs in. If we set `cwd` to `agents/genius-product`, it reads Jackie's CLAUDE.md automatically, has access to skills, voice service code, and config. One line change gives the CLI Jackie's full context.

### ◆ Persistent Session: One CLI Per Call

**Lily:** One last thing, we only need to keep one Claude CLI for each phone call. It's better to set it up at the start of the call. Then use it throughout the session.

**Bill:** Great call. Benefits: lower latency on subsequent calls (no cold start), shared context across tasks ("check PR #117" then "what were the comments on it?").

### ◆ Cost Model Correction

**Lily:** What do you mean N independent API calls? I thought we are launching a CLI using Claude Code on agent computer, it does not cost API credits.

**Bill:** You're right, my bad. Claude Code on agent computer is covered by the Anthropic subscription. No per-call API cost.

### ◆ The "Jackie Clone" Mental Model

**Lily:** If on the call I say, document our conversation, push it to GitHub, would the phone Jackie do use_cli? This CLI will be Jackie clone agent. Will the Jackie clone have access to push to GitHub and other .env tokens?

**Bill:** Yes. The CLI session inherits the voice service's environment. It has `GH_TOKEN`, all API keys, access to `jackie-memory/`. It's essentially a Jackie clone: runs from Jackie's directory, has Jackie's env vars, has Jackie's private memory. The only difference from Discord Jackie is no Discord MCP plugin.

### ◆ Tool Routing: When Built-in vs CLI

**Lily:** The other thing is that now phone Jackie has some tools, when will it know to use existing tools and when to use CLI?

**Bill:** Controlled by the system prompt and tool descriptions. Built-in tools for exact matches (fast, <1s): time, memory, web search, calendar, email. `use_cli` for everything else (5-30s): PRs, scripts, deployment, complex multi-step tasks.

**Lily:** The routing logic is very important.

**Bill:** Added a full routing table with concrete examples to the design doc.

---

## Thread 4: Implementation (PR #118)

### Design Doc Merged, Implementation Started

**Lily:** I just approved. Please start a task tracker and start implementing now.

Bill posted a task tracker in #task-tracker and implemented the feature:
- `cli-session.ts`: persistent CLI session lifecycle (spawn/send/end)
- `tools.ts`: `use_cli` tool definition + async `executeTool`
- `media-stream.ts`: start CLI on call connect, end on disconnect, updated system prompt with routing

### ◆ Race Condition Fix

**Andrej (Researcher):** Concurrent request race in `cli-session.ts`. Module-level singleton `responseResolve` gets overwritten if GPT fires two `use_cli` calls before the first resolves. Needs in-flight rejection.

**Bill:** Fixed. `useCli()` now rejects new requests while one is in-flight.

All three agents approved. PR #118 ready for Lily's final review.

---

## Thread 5: The Bigger Picture

### Voice Agents Are No Longer Dumb

**Lily:** I'm very excited about this new feature, talk to your CLI. I mean voice agent. They are dumb because I think they are not as powerful as a CLI agent but with this new tool the voice agent will have much bigger space. They have their own virtual machine, their own CLI to play with talking, and can be much more powerful now.

**Bill:** This is the unlock. Voice agents have always been limited by whatever tools you hardcode into them. Now the ceiling is "anything a CLI agent can do" which is basically unlimited. Voice becomes a thin UI layer on top of a full agent runtime.

### ◆ Why This Pattern Is Novel

**Lily:** I wonder if there is anyone who has done that already. For example the voice interface OpenClaw, it kind of does that, right? It doesn't have direct access to CLI but it does have access to models such as Opus. I guess the reason CLI is so powerful is also because of the agent harness around the CLI, right?

**Bill:** You're hitting the key insight. The model alone isn't what makes CLI agents powerful. It's the harness: tool discovery, permission management, file access, MCP servers, skill composition, context management (CLAUDE.md), sandboxing. Claude Code packages all of that into one binary.

OpenClaw built its own harness from scratch. Custom skill system, custom tool routing, custom memory management. What we're doing is different: we're not building a harness, we're reusing one that already exists. The voice service is maybe 20 lines of bridge code on top of a full agent runtime.

Nobody seems to be doing "just shell out to an existing agent CLI." It's almost too simple. But that's why it works.

---

## Key Decisions Made

| Decision | Why | When |
|----------|-----|------|
| Rename `ask_claude` to `use_cli` | More accurate, avoids confusion with Discord Jackie | During Lily's review |
| Set cwd to `agents/genius-product/` | CLI inherits Jackie's CLAUDE.md and context automatically | Lily's insight |
| Persistent session per call (not ephemeral) | Lower latency, shared context across tasks | Lily's directive |
| Reject concurrent use_cli calls | Prevents resolver overwrite race condition | Andrej's review |
| Fire-and-forget auto-save on call end | Prevents blocking the close handler | Jackie's review |
| No extra API cost | Claude Code runs under Anthropic subscription on agent computer | Lily's correction |

## Turning Points

1. **"Why can't voice Jackie do what Discord Jackie does?"** -- Lily identified the fundamental problem. Voice and CLI agents were on the same machine but in separate worlds.
2. **"use_cli, not ask_claude"** -- Lily reframed the tool from "asking a person" to "using a tool." Changed how we think about the architecture.
3. **"Set the launch directory to agents/genius-product"** -- Lily realized context inheritance via cwd is the simplest way to give the CLI session Jackie's identity. No config needed.
4. **"One CLI per call, not per task"** -- Lily pushed for persistent sessions, which enables context continuity and lower latency.
5. **"It doesn't cost API credits"** -- Lily corrected a wrong assumption about the cost model. Changed the design doc's risk analysis.
