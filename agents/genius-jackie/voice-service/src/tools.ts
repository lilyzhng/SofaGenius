import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join } from "node:path";
import { config } from "./config.js";

const { dir: jackieDir, memoryDir } = config.jackie;

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
    description: "Search private memory files by keyword.",
    parameters: {
      type: "object",
      properties: {
        keyword: {
          type: "string",
          description: "Keyword to search for in memory files",
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
];

/** Execute a tool call and return the result string */
export function executeTool(name: string, args: Record<string, string>): string {
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

  // Load private memory context
  const contextFile = join(memoryDir, "context.md");
  if (existsSync(contextFile)) {
    parts.push(
      "# Personal Context\n" + readFileSync(contextFile, "utf-8")
    );
  }

  // Load recent call logs
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

  // Load action items
  const actionItems = join(memoryDir, "action-items.md");
  if (existsSync(actionItems)) {
    parts.push(
      "# Open Action Items\n" + readFileSync(actionItems, "utf-8")
    );
  }

  return parts.length > 0
    ? parts.join("\n\n---\n\n")
    : "No context loaded yet — this is a fresh start.";
}

function readMemory(keyword: string): string {
  if (!existsSync(memoryDir)) return "No memory directory found.";

  try {
    const result = execFileSync(
      "grep",
      ["-ril", keyword, memoryDir],
      { encoding: "utf-8", timeout: 10000 }
    ).trim();

    if (!result) return `No memories found matching "${keyword}".`;

    const files = result.split("\n").slice(0, 5);
    const contents = files.map((f) => {
      const content = readFileSync(f, "utf-8").slice(0, 2000);
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
    execFileSync("git", ["add", "context.md", "calls/", "action-items.md"], opts);
    execFileSync("git", ["commit", "-m", message], opts);
    execFileSync("git", ["push"], opts);
    return "Changes committed and pushed to jackie-memory.";
  } catch (e) {
    const err = e as Error & { stderr?: string };
    if (err.stderr?.includes("nothing to commit") || err.stderr?.includes("did not match any files")) {
      return "No changes to commit.";
    }
    return `Git error: ${err.message}`;
  }
}
