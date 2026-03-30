import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from "node:fs";
import { execFileSync, execSync } from "node:child_process";
import { join } from "node:path";
import { config } from "./config.js";
import { useCli } from "./cli-session.js";

const { dir: jackieDir, memoryDir, skillsDir } = config.jackie;

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
    name: "read_memory",
    description: "Search through all of your private memories — past conversations, call summaries, notes, learnings, and vault. Use this PROACTIVELY whenever Lily mentions a person, topic, project, or past event. Don't wait to be asked — if something might have context in your memory, search for it.",
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
    name: "save_call_summary",
    description:
      "Save a call summary after the conversation ends. Includes key topics, decisions, and action items.",
    parameters: {
      type: "object",
      properties: {
        summary: {
          type: "string",
          description: "The call summary in markdown format",
        },
      },
      required: ["summary"],
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
    name: "commit_and_push",
    description:
      "Git add, commit, and push all changes in the private memory repo so other agents can see them.",
    parameters: {
      type: "object",
      properties: {
        message: {
          type: "string",
          description: "Git commit message",
        },
      },
      required: ["message"],
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
    name: "use_cli",
    description:
      "Run a task using the Claude Code CLI on this machine. It has full access to bash, files, git, MCP servers, and all agent skills. Use this when the user asks for something beyond your built-in tools: checking PRs, running scripts, deployment status, complex research, file operations, or anything you can't do with your other tools. This is slower (5-30s) so tell the user you're looking into it BEFORE calling this tool.",
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
    case "read_memory":
      return readMemory(args.keyword);
    case "save_memory":
      return saveMemory(args.content);
    case "save_call_summary":
      return saveCallSummary(args.summary);
    case "create_action_item":
      return createActionItem(args.item, args.assignee);
    case "commit_and_push":
      return commitAndPush(args.message);
    case "get_current_time":
      return getCurrentTime();
    case "web_search":
      return runSkillBridge("jackie-web", `search --query "${args.query}" --count ${args.count ?? 5}`);
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

function readMemory(keyword: string): string {
  if (!existsSync(memoryDir)) return "No memory directory found.";

  // Search across all subdirectories recursively
  try {
    const result = execFileSync(
      "grep",
      ["-ril", "--include=*.md", keyword, memoryDir],
      { encoding: "utf-8", timeout: 10000 }
    ).trim();

    if (!result) return `No memories found matching "${keyword}".`;

    // Prioritize call summaries and notes, then other files
    const allFiles = result.split("\n");
    const prioritized = [
      ...allFiles.filter((f) => f.includes("call-summary") || f.includes("notes")),
      ...allFiles.filter((f) => !f.includes("call-summary") && !f.includes("notes")),
    ].slice(0, 5);

    const contents = prioritized.map((f) => {
      const content = readFileSync(f, "utf-8").slice(0, 3000);
      return `## ${f.replace(memoryDir + "/", "")}\n${content}`;
    });

    return contents.join("\n\n---\n\n");
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

function saveCallSummary(summary: string): string {
  const callsDir = join(memoryDir, "calls");
  mkdirSync(callsDir, { recursive: true });

  const now = new Date();
  const date = now.toISOString().split("T")[0];
  const time = now.toLocaleTimeString("en-US", {
    timeZone: "America/Los_Angeles",
    hour: "2-digit",
    minute: "2-digit",
  });
  const file = join(callsDir, `${date}.md`);

  const entry = `\n\n## Call at ${time} PT\n${summary}`;

  if (existsSync(file)) {
    const existing = readFileSync(file, "utf-8");
    writeFileSync(file, existing + entry);
  } else {
    writeFileSync(file, `# Calls — ${date}${entry}`);
  }

  return `Call summary saved to calls/${date}.md`;
}

function createActionItem(item: string, assignee?: string): string {
  const file = join(memoryDir, "action-items.md");
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

function commitAndPush(message: string): string {
  const opts = { encoding: "utf-8" as const, cwd: memoryDir, timeout: 30000 };
  try {
    execFileSync("git", ["add", "."], opts);
    try {
      execFileSync("git", ["commit", "-m", message], opts);
    } catch (e) {
      const err = e as Error & { stderr?: string };
      if (err.stderr?.includes("nothing to commit")) {
        return "No changes to commit.";
      }
      throw e;
    }
    // Pull with rebase to integrate remote changes before pushing
    try {
      execFileSync("git", ["pull", "--rebase"], opts);
    } catch {
      // If rebase fails, abort and report
      try { execFileSync("git", ["rebase", "--abort"], opts); } catch { /* ignore */ }
      return "Committed locally but could not rebase with remote. Manual intervention needed.";
    }
    execFileSync("git", ["push"], opts);
    return "Changes committed and pushed to jackie-memory.";
  } catch (e) {
    const err = e as Error & { stderr?: string };
    return `Git error: ${err.message}`;
  }
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
