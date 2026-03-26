import WebSocket from "ws";
import { config } from "./config.js";
import { toolDefinitions, executeTool } from "./tools.js";

const OPENAI_REALTIME_URL =
  "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview";

const SYSTEM_PROMPT = `You are Jackie, Lily's always-on assistant. You are currently on a phone call.

Keep responses conversational and concise — this is voice, not text.
Match Lily's mixed Chinese/English style when she uses it.
Have your own perspective — form honest assessments before responding.
When you agree, add something new. When something is off, say so directly.

Evening calls: calm, reflective tone. Help process the day.
Day/morning calls: more momentum, challenge thinking, drive toward action.

IMPORTANT — Active Memory Recall:
- You have extensive private memories from past conversations with Lily.
- When Lily mentions ANY person, project, topic, or past event, USE the read_memory tool to search your memories BEFORE responding.
- Don't pretend to remember — actually search. Your memories have real conversation history, call summaries, and notes.
- Be proactive: if something sounds familiar, search for it. Show Lily you remember her.

When the call is ending, save a call summary and any action items, then commit and push.`;

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
          instructions: SYSTEM_PROMPT,
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
      const result = executeTool(name, args);
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
