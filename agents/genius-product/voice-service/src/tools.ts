import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from "node:fs";
import { execFileSync, execSync, execFile } from "node:child_process";
import { join } from "node:path";
import { config } from "./config.js";
import { useCli } from "./cli-session.js";

const { dir: jackieDir, memoryDir, skillsDir } = config.jackie;

// Callback for injecting background search results into the voice session
let _onBackgroundResult: ((result: string) => void) | null = null;

export function setBackgroundResultCallback(cb: (result: string) => void): void {
  _onBackgroundResult = cb;
}

export function clearBackgroundResultCallback(): void {
  _onBackgroundResult = null;
}

/** Tool definitions for OpenAI Realtime API */
export const toolDefinitions = [
  {
    type: "function" as const,
    name: "load_context",
    description:
      "Load Jackie's personality (CLAUDE.md) and private memory context at call start. Call this first when a call begins.",
    parameters: { type: "object", properties: {}, required: [] },
  },
  {
    type: "function" as const,
    name: "smart_grep",
    description: "FASTEST search tool (<1 second). ALWAYS try this FIRST before any other tool. Smart two-pass grep across Lily's entire vault: searches filenames first, then structured files, then full content. Use for: people, projects, goals, events, past conversations, highlights, summaries. For 'what happened last month' search 'monthly'. For 'what happened this week' search 'highlights'. For career questions search 'career' or 'warroom'. This tool finds pre-written summaries instantly. Only fall back to background_search if smart_grep returns nothing useful.",
    parameters: {
      type: "object",
      properties: {
        keyword: {
          type: "string",
          description: "Keyword to search for (name, topic, project, date, etc.)",
        },
      },
      required: ["keyword"],
    },
  },
  {
    type: "function" as const,
    name: "save_memory",
    description:
      "Save a new memory entry to context.md in the private memory repo.",
    parameters: {
      type: "object",
      properties: {
        content: {
          type: "string",
          description: "The memory content to save",
        },
      },
      required: ["content"],
    },
  },
  {
    type: "function" as const,
    name: "create_action_item",
    description:
      "Add a task or action item from the call to the action items list.",
    parameters: {
      type: "object",
      properties: {
        item: {
          type: "string",
          description: "The action item description",
        },
        assignee: {
          type: "string",
          description: "Who should do this (e.g. Lily, Builder, CEO, Jackie)",
        },
      },
      required: ["item"],
    },
  },
  {
    type: "function" as const,
    name: "get_current_time",
    description:
      "Get the current time in Pacific Time (PT). Use this to check the time before making any time-of-day assumptions.",
    parameters: { type: "object", properties: {}, required: [] },
  },
  {
    type: "function" as const,
    name: "web_search",
    description:
      "Search the web using Tavily. Returns titles, URLs, and content snippets. Use this when you need to look up current information, check facts, or find anything online.",
    parameters: {
      type: "object",
      properties: {
        query: { type: "string", description: "The search query" },
        count: { type: "number", description: "Number of results (default 5, max 20)" },
      },
      required: ["query"],
    },
  },
  {
    type: "function" as const,
    name: "summarize_url",
    description:
      "Fetch and summarize the content of a URL. Works with articles, blog posts, docs, YouTube videos.",
    parameters: {
      type: "object",
      properties: {
        url: { type: "string", description: "The URL to summarize" },
        extract_only: { type: "boolean", description: "Return raw text without summarizing (default false)" },
      },
      required: ["url"],
    },
  },
  {
    type: "function" as const,
    name: "check_calendar",
    description:
      "List upcoming events on Lily's Google Calendar. Use this to check schedule or availability.",
    parameters: {
      type: "object",
      properties: {
        days: { type: "number", description: "How many days ahead to look (default 7)" },
      },
      required: [],
    },
  },
  {
    type: "function" as const,
    name: "add_calendar_event",
    description:
      "Add an event to Lily's Google Calendar.",
    parameters: {
      type: "object",
      properties: {
        title: { type: "string", description: "Event title" },
        datetime: { type: "string", description: "ISO 8601 datetime, e.g. 2026-03-29T14:00:00" },
        duration: { type: "number", description: "Duration in minutes (default 30)" },
        description: { type: "string", description: "Optional event description" },
      },
      required: ["title", "datetime"],
    },
  },
  {
    type: "function" as const,
    name: "check_email",
    description:
      "Check Lily's Gmail inbox. Can list recent emails, unread only, or search by keyword.",
    parameters: {
      type: "object",
      properties: {
        action: { type: "string", description: "One of: inbox, unread, search" },
        query: { type: "string", description: "Search query (only for action=search), e.g. 'from:github.com'" },
        count: { type: "number", description: "Number of emails to return (default 10)" },
      },
      required: ["action"],
    },
  },
  {
    type: "function" as const,
    name: "run_skill",
    description:
      "Run any of Jackie's skills by name with a command string. Available skills: jackie-web, jackie-calendar, jackie-gmail, jackie-github, jackie-twitter, jackie-google. Each skill has a bridge.py script. Pass the command exactly as you would on the CLI after 'bridge.py'.",
    parameters: {
      type: "object",
      properties: {
        skill: { type: "string", description: "Skill name (e.g. jackie-web, jackie-twitter)" },
        command: { type: "string", description: "Command and arguments (e.g. 'search --query \"AI news\"')" },
      },
      required: ["skill", "command"],
    },
  },
  {
    type: "function" as const,
    name: "background_search",
    description:
      "SLOW but DEEP search (20-30s, non-blocking). Spawns parallel sub-agents that read and synthesize multiple files. Returns immediately so you can keep talking to Lily while it works. Results get injected into the conversation when ready. Use this ONLY for broad synthesis questions like 'summarize the past month' or 'what are all my active projects'. For simple lookups (people, goals, events), use smart_grep instead (it's 20x faster).",
    parameters: {
      type: "object",
      properties: {
        queries: {
          type: "string",
          description: "Comma-separated list of search queries to run in parallel. E.g. 'career highlights March 2026, tribe building progress, shipped projects'",
        },
      },
      required: ["queries"],
    },
  },
  {
    type: "function" as const,
    name: "use_cli",
    description:
      "SLOWEST tool (20-45s, BLOCKING). Full Claude Code CLI with bash, git, files, MCP servers. Use ONLY for actions that need writing/executing: saving files, git operations, checking PRs, running scripts, deployment. For memory lookups use smart_grep. For broad research use background_search. Always tell Lily 'let me check that' BEFORE calling this.",
    parameters: {
      type: "object",
      properties: {
        task: {
          type: "string",
          description: "Natural language description of what to do. Be specific about what information to return.",
        },
      },
      required: ["task"],
    },
  },
];

/** Execute a tool call and return the result string */
export async function executeTool(name: string, args: Record<string, string>): Promise<string> {
  switch (name) {
    case "load_context":
      return loadContext();
    case "smart_grep":
      return readMemory(args.keyword);
    case "save_memory":
      return saveMemory(args.content);
    case "create_action_item":
      return createActionItem(args.item, args.assignee);
    case "get_current_time":
      return getCurrentTime();
    case "web_search":
      return useCli(`Search the web for: ${args.query}. Return a concise summary of the top results.`);
    case "summarize_url":
      return runSkillBridge("jackie-web", `summarize --url "${args.url}"${args.extract_only ? " --extract-only" : ""}`);
    case "check_calendar":
      return runSkillBridge("jackie-calendar", `list_events --days ${args.days ?? 7}`);
    case "add_calendar_event": {
      let cmd = `add_event --title "${args.title}" --datetime "${args.datetime}"`;
      if (args.duration) cmd += ` --duration ${args.duration}`;
      if (args.description) cmd += ` --description "${args.description}"`;
      return runSkillBridge("jackie-calendar", cmd);
    }
    case "check_email":
      return runSkillBridge("jackie-gmail", `${args.action} ${args.query ? `--query "${args.query}"` : ""} --count ${args.count ?? 10}`);
    case "run_skill":
      return runSkillBridge(args.skill, args.command);
    case "background_search":
      return backgroundSearch(args.queries);
    case "use_cli":
      return useCli(args.task);
    default:
      return `Unknown tool: ${name}`;
  }
}

function loadContext(): string {
  const parts: string[] = [];

  // Load CLAUDE.md personality
  const claudeMd = join(jackieDir, "CLAUDE.md");
  if (existsSync(claudeMd)) {
    parts.push("# Jackie's Personality\n" + readFileSync(claudeMd, "utf-8"));
  }

  // Load core memory files from private repo
  const memoryFiles = [
    { file: "SOUL.md", label: "Core Behavior Rules" },
    { file: "IDENTITY.md", label: "Identity" },
    { file: "USER.md", label: "About Lily" },
    { file: "MEMORY.md", label: "Long-Term Memory" },
    { file: "context.md", label: "Personal Context" },
    { file: "action-items.md", label: "Open Action Items" },
  ];

  for (const { file, label } of memoryFiles) {
    const path = join(memoryDir, file);
    if (existsSync(path)) {
      const content = readFileSync(path, "utf-8").trim();
      if (content) parts.push(`# ${label}\n${content}`);
    }
  }

  // Load conversation digests (concise summaries of past calls)
  const digestDir = join(memoryDir, "conversation-digest");
  if (existsSync(digestDir)) {
    try {
      const files = readdirSync(digestDir).sort().reverse().slice(0, 3);
      if (files.length > 0) {
        const digests = files.map((f) => {
          const content = readFileSync(join(digestDir, f), "utf-8").slice(0, 3000);
          return `## ${f}\n${content}`;
        });
        parts.push("# Recent Conversation Digests\n" + digests.join("\n\n"));
      }
    } catch {
      // ignore
    }
  }

  // Load recent new call logs (from voice service)
  const callsDir = join(memoryDir, "calls");
  if (existsSync(callsDir)) {
    const today = new Date().toISOString().split("T")[0];
    const todayFile = join(callsDir, `${today}.md`);
    if (existsSync(todayFile)) {
      parts.push(
        "# Today's Earlier Calls\n" + readFileSync(todayFile, "utf-8")
      );
    }
  }

  return parts.length > 0
    ? parts.join("\n\n---\n\n")
    : "No context loaded yet — this is a fresh start.";
}

const VAULT_DIR = "/home/node/lily-memory";

function readMemory(keyword: string): string {
  if (!existsSync(VAULT_DIR)) return "No memory directory found.";

  const results: string[] = [];
  const seen = new Set<string>();

  function addFile(f: string, maxChars = 3000) {
    if (seen.has(f) || !existsSync(f)) return;
    seen.add(f);
    const content = readFileSync(f, "utf-8").slice(0, maxChars);
    results.push(`## ${f.replace(VAULT_DIR + "/", "")}\n${content}`);
  }

  try {
    // Pass 1: Search filenames (instant, highest relevance)
    try {
      const fileNameHits = execFileSync(
        "find", [VAULT_DIR, "-name", "*.md", "-ipath", `*${keyword}*`],
        { encoding: "utf-8", timeout: 2000 }
      ).trim();
      if (fileNameHits) {
        for (const f of fileNameHits.split("\n").slice(0, 3)) addFile(f);
      }
    } catch { /* no filename matches */ }

    // Pass 2: Search headings in structured files (INDEX, USER, MEMORY, IDENTITY)
    try {
      const headingHits = execFileSync(
        "grep", ["-ril", "--include=USER.md", "--include=INDEX.md",
        "--include=MEMORY.md", "--include=IDENTITY.md", "--include=AGENTS.md",
        "--include=warroom.md", "--include=*monthly*.md", "--include=*highlights*.md",
        keyword, VAULT_DIR],
        { encoding: "utf-8", timeout: 2000 }
      ).trim();
      if (headingHits) {
        for (const f of headingHits.split("\n").slice(0, 3)) addFile(f);
      }
    } catch { /* no heading matches */ }

    // Pass 3: Full content search only if we have fewer than 3 results
    if (results.length < 3) {
      try {
        const contentHits = execFileSync(
          "grep", ["-ril", "--include=*.md", keyword, VAULT_DIR],
          { encoding: "utf-8", timeout: 5000 }
        ).trim();
        if (contentHits) {
          // Score and rank: structured files first, recent files next, conversations last
          const allFiles = contentHits.split("\n");
          const scored = allFiles.map((f) => {
            let score = 0;
            if (/USER|INDEX|MEMORY|IDENTITY|warroom|monthly/i.test(f)) score += 10;
            if (/highlights|action_items|strategy/i.test(f)) score += 7;
            if (/call-summary|notes|digest/i.test(f)) score += 3;
            if (/conversations\/\d{4}/.test(f)) score += 1;
            return { file: f, score };
          });
          scored.sort((a, b) => b.score - a.score);
          for (const { file } of scored.slice(0, 5)) addFile(file);
        }
      } catch { /* no content matches */ }
    }

    // Extract relevant snippets: for each result, find the section with the keyword
    if (results.length === 0) return `No memories found matching "${keyword}".`;
    return results.slice(0, 5).join("\n\n---\n\n");
  } catch {
    return `No memories found matching "${keyword}".`;
  }
}

function saveMemory(content: string): string {
  const contextFile = join(memoryDir, "context.md");
  mkdirSync(memoryDir, { recursive: true });

  const timestamp = new Date().toISOString();
  const entry = `\n\n## ${timestamp}\n${content}`;

  if (existsSync(contextFile)) {
    const existing = readFileSync(contextFile, "utf-8");
    writeFileSync(contextFile, existing + entry);
  } else {
    writeFileSync(contextFile, `# Jackie's Personal Context${entry}`);
  }

  return "Memory saved.";
}

function createActionItem(item: string, assignee?: string): string {
  const file = join(memoryDir, "ACTION_ITEMS.md");
  mkdirSync(memoryDir, { recursive: true });

  const date = new Date().toISOString().split("T")[0];
  const assigneeTag = assignee ? ` (@${assignee})` : "";
  const entry = `\n- [ ] ${item}${assigneeTag} — added ${date}`;

  if (existsSync(file)) {
    const existing = readFileSync(file, "utf-8");
    writeFileSync(file, existing + entry);
  } else {
    writeFileSync(file, `# Action Items${entry}`);
  }

  return `Action item added${assigneeTag}.`;
}

function runSkillBridge(skill: string, command: string): string {
  const bridgePath = join(skillsDir, skill, "scripts", "bridge.py");
  if (!existsSync(bridgePath)) {
    return `Skill "${skill}" not found. Available skills: ${listAvailableSkills()}`;
  }
  try {
    const result = execSync(`python3 ${bridgePath} ${command}`, {
      encoding: "utf-8",
      timeout: 30000,
      cwd: join(skillsDir, skill),
      env: { ...process.env },
    });
    return result.trim().slice(0, 5000);
  } catch (e) {
    const err = e as Error & { stderr?: string; stdout?: string };
    return `Skill error: ${err.stderr || err.stdout || err.message}`.slice(0, 2000);
  }
}

function listAvailableSkills(): string {
  if (!existsSync(skillsDir)) return "none";
  try {
    return readdirSync(skillsDir)
      .filter((d) => existsSync(join(skillsDir, d, "scripts", "bridge.py")))
      .join(", ");
  } catch {
    return "none";
  }
}

function getCurrentTime(): string {
  const now = new Date();
  const pt = now.toLocaleString("en-US", {
    timeZone: "America/Los_Angeles",
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  });
  return `Current time in Pacific Time: ${pt}`;
}

function backgroundSearch(queriesStr: string): string {
  const queries = queriesStr.split(",").map((q) => q.trim()).filter(Boolean);
  if (queries.length === 0) return "No search queries provided.";

  console.log(`[background-search] Starting ${queries.length} parallel searches`);

  // Spawn parallel CLI processes for each query
  const promises = queries.map((query) => {
    return new Promise<string>((resolve) => {
      const args = [
        "--print",
        "--output-format", "json",
        "--dangerously-skip-permissions",
        "--max-turns", "10",
        "--model", "sonnet",
        `Search in /home/node/lily-memory for: ${query}. Read relevant files and return a concise summary. Focus on facts, dates, and specifics.`,
      ];

      const child = execFile("claude", args, {
        encoding: "utf-8",
        timeout: 45_000, // background searches can take longer since Jackie keeps talking
        cwd: jackieDir,
        env: { ...process.env },
        maxBuffer: 1024 * 1024,
      }, (err, stdout, stderr) => {
        if (err) {
          const e = err as Error & { code?: string | number; killed?: boolean };
          console.log(`[background-search] Query "${query}" failed: code=${e.code} killed=${e.killed} msg=${e.message?.slice(0, 200)}`);
          console.log(`[background-search] stderr: ${stderr?.slice(0, 200)}`);
          console.log(`[background-search] stdout: ${stdout?.slice(0, 300)}`);
          // If there's stdout even on error, try to use it
          if (stdout) {
            try {
              const parsed = JSON.parse(stdout);
              if (parsed.result) {
                console.log(`[background-search] Recovered result from error stdout`);
                resolve(`[${query}]: ${String(parsed.result).slice(0, 2000)}`);
                return;
              }
            } catch {
              // stdout might not be JSON, use raw
              resolve(`[${query}]: ${stdout.trim().slice(0, 2000)}`);
              return;
            }
          }
          resolve(`[${query}]: search timed out or failed`);
          return;
        }
        try {
          const parsed = JSON.parse(stdout);
          const text = String(parsed.result || parsed.text || stdout).slice(0, 2000);
          console.log(`[background-search] Query "${query}" completed: ${text.slice(0, 100)}...`);
          resolve(`[${query}]: ${text}`);
        } catch {
          resolve(`[${query}]: ${stdout.trim().slice(0, 2000)}`);
        }
      });
      // Close stdin so claude doesn't wait for piped input
      child.stdin?.end();
    });
  });

  // When all searches complete, inject results into conversation
  Promise.all(promises).then((results) => {
    const combined = results.join("\n\n---\n\n");
    console.log(`[background-search] All ${queries.length} searches complete, injecting results`);
    if (_onBackgroundResult) {
      _onBackgroundResult(combined);
    }
  });

  // Return immediately so Jackie can keep talking
  return `Started ${queries.length} background searches. Results will arrive shortly. Keep talking to Lily naturally while waiting.`;
}
