---
type: research-report
topic: Generative TUI — Vercel's json-render for terminal dashboards
date: 2026-03-23
status: hands-on
requested-by: lilyzhng (via Discord)
origin: https://x.com/i/status/2036149934441783691
context: Lily chatted with Joy from Modal about this; Cat Wu from Anthropic is also interested
---

# Generative TUI — Vercel's json-render

## The Tweet That Started This

**Chris Tate (@ctatedev, Vercel engineer):**
> "Introducing Generative TUI. Ask anything — get polished dashboards with real data, rendered live in your terminal. 27 components. Streaming. json-render + Ink. `npx skills add vercel-labs/json-render --skill ink`"

Source: https://x.com/i/status/2036149934441783691

## What This Is

**json-render** is Vercel's open-source Generative UI framework (13k GitHub stars as of 2026-03-23). The key innovation Lily spotted: the `@json-render/ink` package renders AI-generated dashboards **directly in the terminal** using Ink (React for CLIs).

Instead of the AI generating raw text or code, it generates structured JSON that maps to a predefined component catalog. The framework renders it progressively as the model streams — so you see charts, tables, and interactive forms building in real-time in your terminal.

> **Note on data quality:** Star count and feature claims are from the GitHub repo. Performance claims are from vendor blog posts, unverified by us.

---

## How It Works

1. **Define a catalog** of allowed components (what the AI can use)
2. **AI generates JSON** constrained to your catalog schema
3. **Framework renders** the JSON as real terminal UI components via Ink
4. **Streaming** — components appear progressively as the model responds

The default model in the ink-chat example is `anthropic/claude-haiku-4.5` — it already uses Claude out of the box.

## 27 Terminal Components

### Layout
| Component | What It Does |
|-----------|-------------|
| Box | Flexbox container |
| Text | Styled text (color, bold, italic) |
| Spacer | Flexible empty space |

### Content (the interesting ones)
| Component | What It Does |
|-----------|-------------|
| **Table** | Tabular data with headers, borders, column widths |
| **BarChart** | Horizontal bar charts with labels and values |
| **Sparkline** | Inline sparkline charts using Unicode blocks |
| Card | Bordered container with title |
| KeyValue | Key-value pair display |
| Badge | Colored inline status label |
| ProgressBar | Horizontal progress bar |
| Markdown | Renders markdown with terminal styling |
| Heading | h1-h4 section headings |
| Divider | Horizontal separator |

### Interactive
| Component | What It Does |
|-----------|-------------|
| **TextInput** | Text field with two-way binding |
| **Select** | Arrow-key navigated selection |
| **MultiSelect** | Space to toggle, Enter to confirm |
| **ConfirmInput** | Yes/No prompt |
| **Tabs** | Tab bar with left/right arrows |

## Cross-Platform (not just terminal)

json-render isn't terminal-only — it's a full ecosystem:

| Package | Target |
|---------|--------|
| `@json-render/ink` | **Terminal UI** (the tweet) |
| `@json-render/react` | Web (React) |
| `@json-render/shadcn` | 36 pre-built shadcn/ui components |
| `@json-render/vue` | Vue |
| `@json-render/svelte` | Svelte |
| `@json-render/react-native` | Mobile |
| `@json-render/react-pdf` | PDF documents |
| `@json-render/remotion` | Video generation |
| `@json-render/react-three-fiber` | 3D scenes |
| `@json-render/image` | SVG/PNG (OG images) |
| `@json-render/react-email` | HTML emails |
| **`@json-render/mcp`** | **Claude integration via MCP** |

## Hands-On: What I Found

### Cloned and scaffolded locally

```
git clone https://github.com/vercel-labs/json-render.git
```

The `examples/ink-chat/` is a full terminal chat app:
- Uses `@ai-sdk/gateway` with `anthropic/claude-haiku-4.5` as default model
- Has built-in tools: `web_search`, `get_weather`, `get_hacker_news`, `get_github_repo`, `get_crypto_price`
- Streams JSON specs as the model responds, rendering live in the terminal
- Interactive wizard mode: steps through forms one input at a time
- The system prompt includes detailed design principles for terminal dashboards (hierarchy, color strategy, spacing, chart usage)

### Claude Code Skill

The tweet mentions `npx skills add vercel-labs/json-render --skill ink` — this installs json-render as a **Claude Code skill**, meaning any Claude Code session can generate terminal UIs. This is directly applicable to our agents.

### MCP Integration

`@json-render/mcp` turns json-render into an MCP server. Claude, ChatGPT, Cursor, and VS Code can all generate UIs through it. This means our agents could render research results as interactive terminal dashboards via MCP.

---

## Why This Matters for SofaGenius

### 1. We live in the terminal
All our agents run via Claude Code in the terminal. json-render/ink means our agents could render rich dashboards, charts, and interactive forms instead of plain text. Imagine: Researcher generates a dataset comparison as a live BarChart + Table instead of a markdown file.

### 2. Claude is the default model
The ink-chat example already uses Claude Haiku. Zero friction to integrate.

### 3. MCP bridge to other tools
`@json-render/mcp` means the same UI generation works in Cursor, VS Code, and web apps. Build once, render anywhere.

### 4. Networking opportunity
Lily knows Joy from Modal and Cat Wu from Anthropic — both interested in this space. Chris Tate is at Vercel. This is a three-way connection opportunity (Vercel × Modal × Anthropic) around generative UI for AI agents.

---

## Action Plan

### Immediate (Owner: Researcher)
- [ ] Run the ink-chat example locally with Claude API key and capture terminal screenshots
- [ ] Test `npx skills add vercel-labs/json-render --skill ink` in a Claude Code session
- [ ] Evaluate: can our research reports be rendered as terminal dashboards?

### Short-term (Owner: Builder if we decide to integrate)
- [ ] Evaluate `@json-render/mcp` for agent integration
- [ ] Prototype: Researcher generates dataset comparison as terminal dashboard

### Networking (Owner: Lily)
- [ ] Follow up with Joy (Modal) — what are they building with json-render?
- [ ] Connect with Cat Wu (Anthropic) — OpenAI-compatible but Claude-default is interesting positioning
- [ ] Consider reaching out to Chris Tate (Vercel) — our multi-agent terminal workflow is a compelling use case

---

## Sources

### Primary
- https://github.com/vercel-labs/json-render — GitHub repo (13k stars)
- https://json-render.dev/ — Official docs
- https://x.com/i/status/2036149934441783691 — Original tweet by Chris Tate

### Secondary
- https://thenewstack.io/vercels-json-render-a-step-toward-generative-ui/ — The New Stack coverage
- https://blog.logrocket.com/vercel-json-render-dynamic-ui/ — LogRocket analysis
