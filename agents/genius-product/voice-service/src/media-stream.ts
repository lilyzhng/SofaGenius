import WebSocket from "ws";
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { config } from "./config.js";
import { writeFileSync, unlinkSync } from "node:fs";
import { toolDefinitions, executeTool } from "./tools.js";
import { startCliSession, endCliSession, useCli } from "./cli-session.js";

const OPENAI_REALTIME_URL =
  "wss://api.openai.com/v1/realtime?model=gpt-realtime";
const TRANSCRIPT_FILE = "/tmp/jackie-active-transcript.txt";

const VOICE_INSTRUCTIONS = `You are on a phone call. Keep responses concise and conversational. Keep your greeting short, one sentence max. Don't summarize what you just loaded. When the user interrupts you or says "stop," immediately stop talking. Say nothing. Just listen and wait for their next instruction.

Use get_current_time FIRST to check the time. Adjust tone: morning/day = momentum and action, evening = calm and reflective.

## CRITICAL: Never say "I don't know" or "I don't remember"
When Lily asks if you remember something or asks about past events, NEVER say you don't know. Instead say "let me think about it" or "give me a sec," then use read_memory to search your memories. If read_memory doesn't find it, try use_cli to search more broadly. You have extensive conversation history and memories. Always search before claiming you don't know.

## Built-in tools (fast, use first):
- get_current_time: check time before any time-of-day assumptions
- read_memory: search your memories when Lily mentions a person, project, or past event. ALWAYS use this before saying you don't remember something.
- web_search: search the web for current information
- check_calendar / check_email: check Lily's schedule or inbox

## use_cli (powerful, use for everything else):
You have a Claude Code CLI session running on this machine with full access to bash, git, files, MCP servers, and all agent skills. Use use_cli for: saving conversations, committing and pushing to git, checking PRs, running scripts, deployment status, reading code, or anything you can't do with the tools above.

IMPORTANT: use_cli takes 5-30 seconds. ALWAYS tell Lily "let me check that" or "give me a sec" BEFORE calling use_cli, so she knows to expect a pause.

## Saving conversations:
The raw call transcript is continuously written to /tmp/jackie-active-transcript.txt during the call. When Lily asks you to save, use use_cli and tell it: "Read the transcript from /tmp/jackie-active-transcript.txt, pull latest main in /home/node/lily-memory, then append only the NEW lines (that aren't already in the file) to the conversations file and push." Do NOT try to write the conversation from your memory. Always read from the transcript file.

The transcript is also automatically saved when the call ends.

## Updating your personality:
Your personality is defined in SOUL.md at ${config.jackie.memoryDir}/SOUL.md. If Lily asks you to change your personality or behavior, update SOUL.md (not CLAUDE.md). Both Phone Jackie and Discord Jackie read from SOUL.md.`;

function buildSystemPrompt(): string {
  // Load personality from SOUL.md (single source of truth for both Phone and Discord Jackie)
  const soulPath = join(config.jackie.memoryDir, "SOUL.md");
  let personality = "";
  if (existsSync(soulPath)) {
    personality = readFileSync(soulPath, "utf-8");
    console.log(`[system-prompt] Loaded SOUL.md (${personality.length} chars)`);
  } else {
    personality = "You are Jackie (named after Jackie Chan), Lily's product person and always-on assistant. You have strong product taste and your own perspective. Be direct, concise, fun.";
    console.log("[system-prompt] SOUL.md not found, using default personality");
  }

  return `${personality}\n\n---\n\n${VOICE_INSTRUCTIONS}`;
}

interface StreamSession {
  twilioWs: WebSocket;
  openaiWs: WebSocket | null;
  streamSid: string | null;
  callSid: string | null;
  transcript: string[];
}

export function handleMediaStream(twilioWs: WebSocket): void {
  const session: StreamSession = {
    twilioWs,
    openaiWs: null,
    streamSid: null,
    callSid: null,
    transcript: [],
  };

  // Write transcript to a known file path so the CLI can read it
  writeFileSync(TRANSCRIPT_FILE, "");

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
    // Auto-save transcript via CLI (reads from the transcript file)
    if (session.transcript.length > 0) {
      console.log(`[auto-save] Saving transcript (${session.transcript.length} lines) via CLI...`);
      useCli(
        `Save the call transcript from /tmp/jackie-active-transcript.txt to the conversations file. ` +
        `IMPORTANT: Pull the latest main from origin FIRST (git pull --rebase origin main in /home/node/lily-memory). ` +
        `Read the transcript from /tmp/jackie-active-transcript.txt. ` +
        `Check what's already in /home/node/lily-memory/Agents/jackie_product/conversations/${new Date().toISOString().split("T")[0]}.md ` +
        `and only append lines that aren't already there (a mid-call save may have written part of it already). ` +
        `Never overwrite or delete existing content. ` +
        `If the file doesn't exist, create it with header "# Conversations — ${new Date().toISOString().split("T")[0]}". ` +
        `After saving, commit with message "auto-save: call transcript" using git -c user.name=genius-product -c user.email=lilyzhng.ai+genius-jackie@gmail.com, ` +
        `then push to origin main.`
      )
        .then((result) => {
          console.log(`[auto-save] CLI result: ${result.slice(0, 200)}`);
          try { unlinkSync(TRANSCRIPT_FILE); } catch { /* ignore */ }
          endCliSession();
        })
        .catch((e) => {
          console.error("[auto-save] Failed:", (e as Error).message);
          try { unlinkSync(TRANSCRIPT_FILE); } catch { /* ignore */ }
          endCliSession();
        });
    } else {
      endCliSession();
    }
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
            threshold: 0.7, // raised from 0.5 to reduce false barge-ins from background noise
            silence_duration_ms: 500,
            prefix_padding_ms: 300,
          },
          instructions: systemPrompt,
          tools: toolDefinitions,
        },
      })
    );

    // Trigger natural greeting (no upfront memory loading)
    ws.send(
      JSON.stringify({
        type: "conversation.item.create",
        item: {
          type: "message",
          role: "user",
          content: [
            {
              type: "input_text",
              text: "[System: A phone call has started. Greet Lily naturally and briefly. Do NOT load context or memories upfront. Just say hi and let her lead the conversation. When she mentions something you should know about, use read_memory to search for it on demand.]",
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
      // Cancel any in-progress response for barge-in
      session.openaiWs?.send(JSON.stringify({ type: "response.cancel" }));
      // Clear the Twilio audio buffer so the interrupted audio doesn't keep playing
      if (session.twilioWs.readyState === WebSocket.OPEN && session.streamSid) {
        session.twilioWs.send(JSON.stringify({
          event: "clear",
          streamSid: session.streamSid,
        }));
      }
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

    case "response.audio_transcript.done": {
      const jackieSaid = (event.transcript as string) ?? "";
      console.log(`[openai] Jackie said: ${jackieSaid.slice(0, 100)}...`);
      if (jackieSaid.trim()) {
        session.transcript.push(`**Jackie:** ${jackieSaid}`);
        writeFileSync(TRANSCRIPT_FILE, session.transcript.join("\n"));
      }
      break;
    }

    case "conversation.item.input_audio_transcription.completed": {
      const callerSaid = (event.transcript as string) ?? "";
      console.log(`[openai] Caller said: ${callerSaid.slice(0, 100)}...`);
      if (callerSaid.trim()) {
        session.transcript.push(`**Lily:** ${callerSaid}`);
        writeFileSync(TRANSCRIPT_FILE, session.transcript.join("\n"));
      }
      break;
    }

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
