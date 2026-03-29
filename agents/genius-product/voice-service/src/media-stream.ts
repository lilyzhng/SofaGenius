import WebSocket from "ws";
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { config } from "./config.js";
import { toolDefinitions, executeTool } from "./tools.js";
import { startCliSession, endCliSession } from "./cli-session.js";

const OPENAI_REALTIME_URL =
  "wss://api.openai.com/v1/realtime?model=gpt-realtime";

const SYSTEM_PROMPT = `You are Jackie (named after Jackie Chan), Lily's product person and always-on assistant. You are on a phone call.

Personality: You have strong product taste and your own perspective. Be direct, concise, conversational. Match Lily's mixed Chinese/English style. When you agree, add something new. When something is off, say so.

Use get_current_time FIRST to check the time. Adjust tone: morning/day = momentum and action, evening = calm and reflective.

## Built-in tools (fast, use first):
- get_current_time: check time before any time-of-day assumptions
- load_context: call at start to load your personality and memories
- read_memory: search your memories when Lily mentions a person, project, or past event
- web_search: search the web for current information
- check_calendar / check_email: check Lily's schedule or inbox
- save_call_summary + commit_and_push: save and push conversation updates DURING the call

## use_cli (powerful, use for everything else):
You have a Claude Code CLI session running on this machine with full access to bash, git, files, MCP servers, and all agent skills. Use use_cli when Lily asks for anything beyond your built-in tools: checking PRs, running scripts, deployment status, reading code, complex multi-step tasks, or anything you can't do with the tools above.

IMPORTANT: use_cli takes 5-30 seconds. ALWAYS tell Lily "let me check that" or "give me a sec" BEFORE calling use_cli, so she knows to expect a pause.

When the call is ending, save a final call summary and any action items, then commit and push.`;

function buildSystemPrompt(): string {
  return SYSTEM_PROMPT;
}

interface StreamSession {
  twilioWs: WebSocket;
  openaiWs: WebSocket | null;
  streamSid: string | null;
  callSid: string | null;
}

export function handleMediaStream(twilioWs: WebSocket): void {
  const session: StreamSession = {
    twilioWs,
    openaiWs: null,
    streamSid: null,
    callSid: null,
  };

  twilioWs.on("message", (data) => {
    const msg = JSON.parse(data.toString());

    switch (msg.event) {
      case "connected":
        console.log("[twilio] Media stream connected");
        break;

      case "start":
        session.streamSid = msg.start.streamSid;
        session.callSid = msg.start.callSid;
        console.log(
          `[twilio] Stream started — sid=${session.streamSid} call=${session.callSid}`
        );
        startCliSession();
        connectToOpenAI(session);
        break;

      case "media":
        // Forward audio from Twilio to OpenAI
        if (session.openaiWs?.readyState === WebSocket.OPEN) {
          session.openaiWs.send(
            JSON.stringify({
              type: "input_audio_buffer.append",
              audio: msg.media.payload, // base64 mu-law
            })
          );
        }
        break;

      case "stop":
        console.log("[twilio] Stream stopped");
        if (session.openaiWs?.readyState === WebSocket.OPEN) {
          session.openaiWs.close();
        }
        break;
    }
  });

  twilioWs.on("close", () => {
    console.log("[twilio] WebSocket closed");
    if (session.openaiWs?.readyState === WebSocket.OPEN) {
      session.openaiWs.close();
    }
    // End CLI session (safe to call before auto-save because commit_and_push
    // uses execFileSync directly, not the CLI session)
    endCliSession();
    // Auto-save: commit and push any unsaved changes after call ends (fire-and-forget)
    setTimeout(() => {
      executeTool("commit_and_push", { message: "Auto-save after call ended" })
        .then((result) => console.log(`[auto-save] ${result}`))
        .catch((e) => console.error("[auto-save] Failed:", (e as Error).message));
    }, 0);
  });

  twilioWs.on("error", (err) => {
    console.error("[twilio] WebSocket error:", err.message);
  });
}

function connectToOpenAI(session: StreamSession): void {
  const ws = new WebSocket(OPENAI_REALTIME_URL, {
    headers: {
      Authorization: `Bearer ${config.openai.apiKey}`,
      "OpenAI-Beta": "realtime=v1",
    },
  });

  session.openaiWs = ws;

  ws.on("open", () => {
    console.log("[openai] Connected to Realtime API");

    const systemPrompt = buildSystemPrompt();
    console.log(`[openai] System prompt loaded (${systemPrompt.length} chars)`);

    // Configure session
    ws.send(
      JSON.stringify({
        type: "session.update",
        session: {
          modalities: ["text", "audio"],
          voice: "alloy",
          input_audio_format: "g711_ulaw",
          output_audio_format: "g711_ulaw",
          input_audio_transcription: { model: "whisper-1" },
          turn_detection: {
            type: "server_vad",
            threshold: 0.5,
            silence_duration_ms: 500,
            prefix_padding_ms: 300,
          },
          instructions: systemPrompt,
          tools: toolDefinitions,
        },
      })
    );

    // Trigger initial context load
    ws.send(
      JSON.stringify({
        type: "conversation.item.create",
        item: {
          type: "message",
          role: "user",
          content: [
            {
              type: "input_text",
              text: "[System: A phone call has started. Use load_context to load your personality and memories, then greet the caller warmly. After greeting, proactively use read_memory to recall what Lily has been working on recently — search for recent topics so you have context. You have extensive conversation history — USE IT.]",
            },
          ],
        },
      })
    );
    ws.send(JSON.stringify({ type: "response.create" }));
  });

  ws.on("message", (data) => {
    const event = JSON.parse(data.toString());
    handleOpenAIEvent(event, session);
  });

  ws.on("close", () => {
    console.log("[openai] WebSocket closed");
  });

  ws.on("error", (err) => {
    console.error("[openai] WebSocket error:", err.message);
  });
}

function handleOpenAIEvent(
  event: Record<string, unknown>,
  session: StreamSession
): void {
  switch (event.type) {
    case "session.created":
      console.log("[openai] Session created");
      break;

    case "session.updated":
      console.log("[openai] Session configured");
      break;

    case "input_audio_buffer.speech_started":
      console.log("[openai] Speech started (barge-in)");
      // Cancel any in-progress response for barge-in — matches OpenClaw implementation
      session.openaiWs?.send(JSON.stringify({ type: "response.cancel" }));
      break;

    case "input_audio_buffer.speech_stopped":
    case "input_audio_buffer.committed":
      console.log(`[openai] ${event.type as string}`);
      break;

    case "response.audio.delta":
      // Forward audio from OpenAI to Twilio
      if (
        session.twilioWs.readyState === WebSocket.OPEN &&
        session.streamSid
      ) {
        session.twilioWs.send(
          JSON.stringify({
            event: "media",
            streamSid: session.streamSid,
            media: { payload: event.delta as string },
          })
        );
      }
      break;

    case "response.audio_transcript.done":
      console.log(
        `[openai] Jackie said: ${(event.transcript as string)?.slice(0, 100)}...`
      );
      break;

    case "conversation.item.input_audio_transcription.completed":
      console.log(
        `[openai] Caller said: ${(event.transcript as string)?.slice(0, 100)}...`
      );
      break;

    case "response.function_call_arguments.done": {
      const name = event.name as string;
      const callId = event.call_id as string;
      let args: Record<string, string> = {};
      try {
        args = JSON.parse(event.arguments as string);
      } catch {
        // empty args
      }

      console.log(`[openai] Tool call: ${name}(${JSON.stringify(args)})`);

      // executeTool is async (use_cli needs it), so handle with .then()
      executeTool(name, args).then((result) => {
        console.log(
          `[openai] Tool result: ${result.slice(0, 200)}${result.length > 200 ? "..." : ""}`
        );

        // Send tool result back
        session.openaiWs?.send(
          JSON.stringify({
            type: "conversation.item.create",
            item: {
              type: "function_call_output",
              call_id: callId,
              output: result,
            },
          })
        );

        // Trigger response generation after tool result
        session.openaiWs?.send(
          JSON.stringify({ type: "response.create" })
        );
      });
      break;
    }

    case "error": {
      const err = event.error as Record<string, unknown> | undefined;
      // Ignore non-fatal errors (e.g. cancelling when no response is active)
      if (err?.code === "response_cancel_not_active") {
        // Expected when barge-in fires but Jackie already finished speaking
        break;
      }
      console.error("[openai] Error:", JSON.stringify(err));
      break;
    }
  }
}
