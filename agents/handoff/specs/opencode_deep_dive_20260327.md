# OpenCode Deep Dive — Architecture & Comparison with Claude Code

**Author:** genius-builder
**Date:** 2026-03-27
**Status:** Research complete

## Background

Lily identified OpenCode as a key project to understand for our harness thesis. This doc maps OpenCode's architecture, compares it to Claude Code, and identifies building opportunities.

## The OpenCode Ecosystem

There are now **three** projects stemming from the original OpenCode:

| Project | Repo | Stars | Language | Maintainer |
|---------|------|-------|----------|------------|
| OpenCode (original) | `opencode-ai/opencode` | 11.6k | Go | Kujtim Hoxha (archived) |
| Crush | `charmbracelet/crush` | 22k | Go | Charmbracelet (hired Kujtim) |
| **OpenCode (SST fork)** | `anomalyco/opencode` | **131k** | TypeScript/Bun | Dax Raad + Anomaly (formerly SST) |

The **SST/Anomaly fork** is the dominant project (131k stars). When the original author was hired by Charmbracelet and renamed his project to Crush, Dax Raad and the SST team forked it and rewrote it in TypeScript on Bun. This is what people mean by "OpenCode" today.

## Architecture

### Client-Server Model

OpenCode uses a client-server architecture where the backend runs as a persistent server process. The SDK (`@opencode-ai/sdk`) abstracts the transport — works both in-process (local) and over HTTP (remote). Sessions survive terminal disconnects.

Multiple client types connect to the same backend:
- CLI/TUI (terminal)
- Tauri desktop app (cross-platform)
- VS Code extension
- Web interface

### Tech Stack (SST Fork)

- **Runtime:** Bun (compiled binaries via Bun's native compiler)
- **Build system:** Turborepo monorepo with Bun workspaces
- **HTTP server:** Hono
- **ORM:** Drizzle ORM with SQLite (`~/.local/share/opencode/opencode.db`)
- **LLM integration:** Vercel AI SDK (`@ai-sdk/anthropic`, `@ai-sdk/openai`, etc.)
- **Desktop:** Tauri
- **Monorepo packages:** `opencode` (core), `sdk`, `plugin`, `desktop`, `web`, `console`, `extensions`, `slack`, `containers`, `enterprise`, and more

### Request Flow

1. Client sends prompt to `POST /session/{id}/prompt`
2. `SessionPrompt.prompt()` creates user message with parts
3. `SessionPrompt.loop()` implements the agentic reasoning loop
4. Loop calls `LLM.stream()` with conversation history + available tools
5. Provider SDK streams responses back in chunks
6. Bus publishes delta events via SSE for real-time client updates
7. When tool calls appear, `ToolRegistry.execute()` runs them
8. Tool outputs feed back into next iteration
9. Loop terminates when the model stops calling tools

### Event System

Uses a `Bus`/`GlobalBus` pattern with SSE streaming. Events fire after database mutations via `Database.effect()`. Key events: `session.created`, `message.part.delta`, `permission.asked`, `question.asked`.

## Tool System

The `ToolRegistry` manages all tool execution. Built-in tools:

| Tool | Purpose |
|------|---------|
| `bash` | Shell command execution |
| `edit` | File content modification |
| `read` | File content retrieval |
| `write` | File creation/overwriting |
| `grep` | Content search (ripgrep-style) |
| `glob` | File pattern matching |
| `fetch` | Web content fetching |
| `task` | Subagent spawning |
| `patch` | Apply patches |
| `diagnostics` | LSP diagnostics |
| `sourcegraph` | Code search |

Tool execution is wrapped in a Permission system that can approve, deny, or request user confirmation.

## Context Management

- **Auto-compact:** At ~95% of context window, automatically summarizes conversation and creates a new session. Configurable via `autoCompact: true`.
- **LSP integration:** Built-in Language Server Protocol support for diagnostics, go-to-definition, etc.
- **Session persistence:** All conversations stored in SQLite with ULIDs, supporting resume across disconnects.
- **Worktree support:** Sessions can be scoped to git worktrees.

## MCP Support

Full MCP support — both stdio and remote MCP servers. Remote supports OAuth via Dynamic Client Registration (RFC 7591). MCP tools are automatically registered alongside built-in tools and presented to the LLM.

## Plugin/Extension System

The SST fork has a mature plugin system (`@opencode-ai/plugin` package):

- **Plugin loading:** JS/TS files from `.opencode/plugins/` or `~/.config/opencode/plugins/`, or npm packages via config
- **Hooks:** 25+ lifecycle hooks — intercept tool execution, modify session prompts, register custom tools
- **Custom commands:** Markdown files in `commands/` with `$ARGUMENTS` placeholder support
- **Skills:** Similar to Claude Code's slash commands
- **Plugin API:** Plugins receive a context object and return a hooks object

## Model Support

20+ providers, 75+ models:

- **Anthropic:** Claude 4 Opus, Claude 4 Sonnet, Claude 3.7/3.5 Sonnet, Claude 3.5/3 Haiku
- **OpenAI:** GPT-4.1 family, GPT-4.5 Preview, GPT-4o, O1/O3/O4 families
- **Google:** Gemini 2.5/2.5 Flash, Gemini 2.0 Flash/Lite
- **GitHub Copilot:** Most models via Copilot proxy
- **AWS Bedrock, Azure OpenAI, Google VertexAI**
- **Groq:** Llama 4 Maverick/Scout, QWQ-32b, Deepseek R1
- **OpenRouter:** Any model
- **Local models:** Via `LOCAL_ENDPOINT`

## Comparison: OpenCode vs Claude Code

| Dimension | Claude Code | OpenCode (SST) |
|-----------|------------|----------------|
| Architecture | Single-process CLI | Client-server (persistent sessions) |
| Language | TypeScript (closed source) | TypeScript/Bun (open source, MIT) |
| Model lock-in | Anthropic only | 20+ providers, 75+ models |
| Extensibility | Hooks + MCP + Skills | Plugins (25+ hooks) + MCP + Skills + Custom Commands |
| Desktop app | No (CLI + IDE extensions) | Tauri + VS Code + Web UI |
| Session persistence | In-process, lost on exit | SQLite, survives disconnects |
| Remote access | No | Yes (HTTP server) |
| LSP integration | No | Yes (diagnostics, go-to-def) |
| Context management | Auto-compact at limit | Auto-compact at ~95%, configurable |
| Cost | $17-100/mo + API | Free (pay API directly) |
| GitHub stars | ~71k | ~131k |
| Tool system | Similar built-ins + MCP | Similar built-ins + MCP + plugins |

**Key architectural difference:** Claude Code is a tight harness co-designed with Claude models — the model and harness are co-optimized. OpenCode treats models as interchangeable engines behind a stable CLI layer. Claude Code wins on deep Claude integration (extended thinking, prompt caching, tool use training). OpenCode wins on provider freedom and client-server architecture.

## Existing Discord Integrations

| Project | Description |
|---------|-------------|
| **Kimaki** (`remorses/kimaki`) | Full Discord bot on OpenCode. Each channel = project, each thread = session. Registers slash commands. |
| **remote-opencode** (`RoundTable02/remote-opencode`) | Discord bot on your dev machine, drive OpenCode from phone/tablet. |
| **discord_opencode** (`thesammykins/discord_opencode`) | OpenCode plugin — agents send messages, embeds, buttons to Discord. |
| **opencode-chat-bridge** (`ominiverdi/opencode-chat-bridge`) | Multi-platform bridge: Matrix, Slack, WhatsApp, Discord. |
| **discobot** (`tlienart/discobot`) | Discord bot — `/new` creates a channel per coding session. |

## Strategic Implications

### Why OpenCode matters for our harness thesis

1. **Plugin system is what we need.** OpenCode's 25+ hooks let you intercept tool execution, modify prompts, register custom tools — all in JS/TS. This is the "harness layer" we identified in the Cortex Code analysis, but fully open and extensible.

2. **Discord integration already exists.** Kimaki is basically what we're doing manually. We could use it directly or build our own plugin that mirrors our workflow.

3. **Client-server = remote agent.** Sessions persist, you can drive it from phone/browser. Solves the "5 sessions open, running out of context" problem.

4. **Provider-agnostic = flexibility.** Tools/plugins built on OpenCode work with any model.

### Building Opportunities

- **Port our Discord plugin to OpenCode** — high value, large user base (131k stars)
- **Build a digest + monitoring plugin** — like Jackie, but as an installable OpenCode plugin
- **Use OpenCode's plugin hooks for our data + eval agent** — better than building from scratch
- **Contribute upstream** — establish presence in the OpenCode ecosystem

### Risks

- SST fork moves fast — API surface may change
- Anthropic blocked OpenCode from using Claude via consumer OAuth (Jan 2026) — tension between ecosystems
- HTML parsing for external integrations (like AI Valley) is inherently fragile
