import { spawn, ChildProcess } from "node:child_process";
import { config } from "./config.js";
import { randomUUID } from "node:crypto";

let cliProcess: ChildProcess | null = null;
let responseBuffer = "";
let responseResolve: ((result: string) => void) | null = null;
let responseTimeout: ReturnType<typeof setTimeout> | null = null;

/** Start a persistent CLI session for the duration of a phone call */
export function startCliSession(): void {
  if (cliProcess) {
    console.log("[cli-session] Session already running, skipping start");
    return;
  }

  const sessionId = randomUUID();
  const cwd = config.jackie.dir;

  console.log(`[cli-session] Starting persistent CLI session (id=${sessionId}, cwd=${cwd})`);

  cliProcess = spawn("claude", [
    "--print",
    "--input-format", "stream-json",
    "--output-format", "stream-json",
    "--session-id", sessionId,
    "--dangerously-skip-permissions",
    "--max-turns", "10",
  ], {
    cwd,
    env: {
      ...process.env,
      CLAUDE_CODE_ENTRYPOINT: "voice-bridge",
    },
    stdio: ["pipe", "pipe", "pipe"],
  });

  cliProcess.stdout?.on("data", (chunk: Buffer) => {
    const lines = chunk.toString().split("\n");
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const event = JSON.parse(line);
        handleCliEvent(event);
      } catch {
        // Partial JSON line, accumulate
      }
    }
  });

  cliProcess.stderr?.on("data", (chunk: Buffer) => {
    console.error(`[cli-session] stderr: ${chunk.toString().trim()}`);
  });

  cliProcess.on("exit", (code) => {
    console.log(`[cli-session] Process exited with code ${code}`);
    cliProcess = null;
    // If there's a pending response, resolve it with an error
    if (responseResolve) {
      responseResolve("CLI session ended unexpectedly. Please try again.");
      responseResolve = null;
    }
  });

  cliProcess.on("error", (err) => {
    console.error(`[cli-session] Process error: ${err.message}`);
    cliProcess = null;
    if (responseResolve) {
      responseResolve(`CLI session error: ${err.message}`);
      responseResolve = null;
    }
  });
}

function handleCliEvent(event: Record<string, unknown>): void {
  // Extract text content from stream events
  if (event.type === "assistant") {
    // Final assistant message with complete content
    const message = event.message as Record<string, unknown> | undefined;
    const content = message?.content as Array<Record<string, unknown>> | undefined;
    if (content) {
      const textParts = content
        .filter((c) => c.type === "text")
        .map((c) => c.text as string);
      if (textParts.length > 0) {
        responseBuffer = textParts.join("\n");
      }
    }
  }

  // result event signals the final output
  if (event.type === "result") {
    const result = event.result as string | undefined;
    if (result) {
      responseBuffer = result;
    }
    finishResponse();
  }
}

function finishResponse(): void {
  if (responseResolve) {
    const result = responseBuffer.trim() || "Task completed (no output).";
    responseResolve(result.slice(0, 3000));
    responseResolve = null;
    responseBuffer = "";
  }
  if (responseTimeout) {
    clearTimeout(responseTimeout);
    responseTimeout = null;
  }
}

/** Send a task to the persistent CLI session and wait for the result.
 *  Rejects concurrent requests: only one use_cli call can be in-flight at a time.
 *  This prevents the race condition where a second call overwrites the first's resolver. */
export function useCli(task: string): Promise<string> {
  return new Promise((resolve) => {
    if (responseResolve) {
      // Another use_cli call is already in-flight. Reject this one immediately
      // rather than silently overwriting the previous resolver.
      resolve("Another CLI task is already running. Please wait for it to finish.");
      return;
    }

    if (!cliProcess || !cliProcess.stdin?.writable) {
      // Try to start a new session if none exists
      startCliSession();
      if (!cliProcess || !cliProcess.stdin?.writable) {
        resolve("CLI session is not available. Could not start a new session.");
        return;
      }
    }

    // Set up response handler
    responseBuffer = "";
    responseResolve = resolve;

    // Set timeout (60s max per task)
    responseTimeout = setTimeout(() => {
      if (responseResolve) {
        const partial = responseBuffer.trim();
        responseResolve(
          partial
            ? `Task timed out. Partial result: ${partial.slice(0, 2000)}`
            : "Task timed out with no response."
        );
        responseResolve = null;
        responseBuffer = "";
      }
    }, 60_000);

    // Send the task
    const message = JSON.stringify({ prompt: task }) + "\n";
    console.log(`[cli-session] Sending task: ${task.slice(0, 100)}...`);
    cliProcess.stdin.write(message);
  });
}

/** Kill the CLI session when the call ends */
export function endCliSession(): void {
  if (cliProcess) {
    console.log("[cli-session] Ending CLI session");
    try {
      cliProcess.stdin?.end();
      cliProcess.kill("SIGTERM");
    } catch {
      // Process may already be dead
    }
    cliProcess = null;
    responseBuffer = "";
    if (responseResolve) {
      responseResolve("CLI session ended.");
      responseResolve = null;
    }
    if (responseTimeout) {
      clearTimeout(responseTimeout);
      responseTimeout = null;
    }
  }
}
