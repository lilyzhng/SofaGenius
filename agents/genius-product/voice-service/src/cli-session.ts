import { execFileSync } from "node:child_process";
import { config } from "./config.js";
import { randomUUID } from "node:crypto";

let sessionId: string | null = null;

/** Start a CLI session ID for the duration of a phone call.
 *  The actual CLI process is spawned per-task using --resume to maintain context. */
export function startCliSession(): void {
  sessionId = randomUUID();
  console.log(`[cli-session] Session initialized (id=${sessionId})`);
}

/** Send a task to the CLI and wait for the result.
 *  Each call spawns a short-lived `claude --print` process.
 *  Context is preserved across calls via --resume <session-id>. */
export async function useCli(task: string): Promise<string> {
  if (!sessionId) {
    startCliSession();
  }

  const cwd = config.jackie.dir;
  const isFirstCall = !usedBefore;
  usedBefore = true;

  const args = [
    "--print",
    "--output-format", "json",
    "--dangerously-skip-permissions",
    "--max-turns", "10",
  ];

  // First call uses --session-id, subsequent calls use --resume
  if (isFirstCall) {
    args.push("--session-id", sessionId!);
  } else {
    args.push("--resume", sessionId!);
  }

  args.push(task);

  console.log(`[cli-session] Running task (session=${sessionId}, first=${isFirstCall}): ${task.slice(0, 100)}...`);

  try {
    const result = execFileSync("claude", args, {
      encoding: "utf-8",
      timeout: 45_000, // 45s max for blocking CLI calls
      cwd,
      env: { ...process.env },
      maxBuffer: 1024 * 1024, // 1MB
    });

    // Parse the JSON result
    try {
      const parsed = JSON.parse(result);
      const text = parsed.result || parsed.text || result;
      console.log(`[cli-session] Task completed: ${String(text).slice(0, 200)}...`);
      return String(text).slice(0, 3000);
    } catch {
      // If JSON parsing fails, return raw output
      console.log(`[cli-session] Task completed (raw): ${result.slice(0, 200)}...`);
      return result.trim().slice(0, 3000);
    }
  } catch (err: unknown) {
    const error = err as Error & { stderr?: string; stdout?: string };
    const stderr = error.stderr || "";
    const stdout = error.stdout || "";
    console.error(`[cli-session] Task failed: ${error.message?.slice(0, 200)}`);
    if (stderr) console.error(`[cli-session] stderr: ${stderr.slice(0, 500)}`);

    // Try to parse stdout even on error (might have partial result)
    if (stdout) {
      try {
        const parsed = JSON.parse(stdout);
        if (parsed.result) return String(parsed.result).slice(0, 3000);
      } catch {
        // ignore
      }
      return stdout.trim().slice(0, 3000);
    }

    // Return a natural message so the voice model can respond intelligently
    if (error.message?.includes("ETIMEDOUT") || error.message?.includes("timed out")) {
      return "The search took too long and timed out. Tell Lily it's taking too long and suggest a more specific question or offer to try again.";
    }
    return `The tool encountered an error: ${error.message?.slice(0, 200)}. Let Lily know and offer to try a different approach.`;
  }
}

let usedBefore = false;

/** End the CLI session when the call ends */
export function endCliSession(): void {
  if (sessionId) {
    console.log(`[cli-session] Session ended (id=${sessionId})`);
    sessionId = null;
    usedBefore = false;
  }
}
