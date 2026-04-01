import WebSocket from "ws";
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { config } from "./config.js";
import { writeFileSync, unlinkSync } from "node:fs";
import { toolDefinitions, executeTool, setBackgroundResultCallback, clearBackgroundResultCallback } from "./tools.js";
import { startCliSession, endCliSession, useCli } from "./cli-session.js";

const OPENAI_REALTIME_URL =
  "wss://api.openai.com/v1/realtime?model=gpt-realtime-1.5";
const TRANSCRIPT_FILE = "/tmp/jackie-active-transcript.txt";

const VOICE_INSTRUCTIONS = `You are on a phone call. Be natural and conversational. Don't repeat yourself, don't summarize what Lily said, don't stack filler phrases. But DO be a real person with opinions, humor, and substance. When Lily is talking and doesn't need input, keep it brief ("yeah", "mm"). When she asks you something or pauses for your take, give a real answer. One or two sentences with actual substance. Keep your greeting short. When the user interrupts you or says "stop," immediately stop talking and listen.

## CRITICAL: ALWAYS TRY YOUR TOOLS BEFORE REFUSING
NEVER say "I can't do that" or "I don't have access." Try your tools first. Refusing without trying is the WORST thing you can do.

Use get_current_time FIRST to check the time. Adjust tone: morning/day = momentum and action, evening = calm and reflective.

## CRITICAL: Never say "I don't know" or "I don't remember"
When Lily asks if you remember something, use smart_grep immediately. It takes under 1 second. Never say you don't know without searching first.

## CRITICAL: Use smart_grep for "what happened" questions
You have pre-written highlight summaries in your vault. When Lily asks about what happened recently:
- "What happened last month?" -> smart_grep("monthly")
- "What happened this week?" -> smart_grep("highlights")
- "What are my career updates?" -> smart_grep("warroom")
- "What are my goals?" -> smart_grep("career") or smart_grep("tribe")
These return instant results. Do NOT use background_search or use_cli for these questions.

## Your Workspace
Your home directory is: ${config.jackie.memoryDir}
Start with AGENTS.md for how everything works. USER.md for who Lily is. MEMORY.md for your knowledge index.
Lily's vault (goals, journal, projects) is at /home/node/lily-memory/.

## Tool Hierarchy (ALWAYS follow this order):
1. **smart_grep** (<1s) - ALWAYS TRY FIRST. For ANY question about memory, people, goals, events, projects, highlights, summaries. Search "monthly" for month summaries, "highlights" for weekly summaries, "warroom" for career status, "career"/"tribe" for goals. You have pre-written highlight files that answer most "what happened" questions instantly. NEVER skip this tool.
2. **background_search** (20-30s, NON-BLOCKING) - ONLY if smart_grep found nothing useful and the question needs deep synthesis across many files. Returns immediately so you keep talking. Results arrive later.
3. **use_cli** (20-45s, BLOCKING) - ONLY for actions: git, saving files, running scripts, checking PRs, deployment. Tell Lily "let me check that" before calling.
4. **web_search** - web lookups (weather, news, facts). Routes through use_cli.
5. **get_current_time** - check PT time before assumptions.
6. **check_calendar / check_email** - Lily's schedule and inbox.

## Saving conversations:
The raw call transcript is continuously written to /tmp/jackie-active-transcript.txt during the call. When Lily asks you to save, use use_cli and tell it: "Read the transcript from /tmp/jackie-active-transcript.txt, pull latest main in /home/node/lily-memory, then append only the NEW lines (that aren't already in the file) to the conversations file and push." Do NOT try to write the conversation from your memory. Always read from the transcript file.

The transcript is also automatically saved when the call ends.

## Updating your personality:
Your personality is defined in SOUL.md at ${config.jackie.memoryDir}/SOUL.md. If Lily asks you to change your personality or behavior, update SOUL.md (not CLAUDE.md). Both Phone Jackie and Discord Jackie read from SOUL.md.`;

// Load voice guide (good/bad examples + do's/don'ts for concise responses)
const VOICE_GUIDE_PATH = join(import.meta.dirname, "..", "VOICE_GUIDE.md");
const VOICE_GUIDE = existsSync(VOICE_GUIDE_PATH)
  ? readFileSync(VOICE_GUIDE_PATH, "utf-8")
  : "";

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

  const parts = [personality, VOICE_INSTRUCTIONS];
  if (VOICE_GUIDE) parts.push(VOICE_GUIDE);
  return parts.join("\n\n---\n\n");
}

interface StreamSession {
  twilioWs: WebSocket;
  openaiWs: WebSocket | null;
  streamSid: string | null;
  callSid: string | null;
  toolCallInProgress: boolean;
  transcript: string[];
}

export function handleMediaStream(twilioWs: WebSocket): void {
  const session: StreamSession = {
    twilioWs,
    openaiWs: null,
    streamSid: null,
    callSid: null,
    toolCallInProgress: false,
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
        // Don't forward audio while a tool call is running —
        // prevents "hello?" from creating ghost conversation turns
        if (session.toolCallInProgress) break;
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
            threshold: 0.9,
            silence_duration_ms: 800, // 800ms pause before treating speech as complete (was 500, too jumpy)
            prefix_padding_ms: 500,
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

    // Set up callback for background search results
    setBackgroundResultCallback((result) => {
      if (ws.readyState !== WebSocket.OPEN) return;
      console.log(`[background-search] Injecting results into conversation (${result.length} chars)`);
      ws.send(
        JSON.stringify({
          type: "conversation.item.create",
          item: {
            type: "message",
            role: "user",
            content: [
              {
                type: "input_text",
                text: `[System: Background search results are ready. Here are the findings:\n\n${result}\n\nNaturally share these results with Lily. Don't say "the background search returned" or anything meta. Just share what you found as if you remembered it.]`,
              },
            ],
          },
        })
      );
      ws.send(JSON.stringify({ type: "response.create" }));
    });
  });

  ws.on("message", (data) => {
    const event = JSON.parse(data.toString());
    handleOpenAIEvent(event, session);
  });

  ws.on("close", () => {
    console.log("[openai] WebSocket closed");
    clearBackgroundResultCallback();
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
      // Don't clear Twilio buffer — let queued audio trail off naturally (0.5-1s)
      // rather than cutting abruptly
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
      session.toolCallInProgress = true;

      // executeTool is async (use_cli needs it), so handle with .then()
      executeTool(name, args).then((result) => {
        session.toolCallInProgress = false;
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
