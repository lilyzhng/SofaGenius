import Fastify from "fastify";
import { WebSocketServer, WebSocket } from "ws";
import { createServer } from "node:http";
import { config } from "./config.js";
import { handleMediaStream } from "./media-stream.js";

function escapeXml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&apos;");
}

export async function startServer(): Promise<void> {
  const { port, publicUrl } = config.server;

  // Create raw HTTP server so we can attach WebSocket to it
  const httpServer = createServer();

  // Fastify for HTTP routes (Twilio webhooks)
  const app = Fastify({ serverFactory: (handler) => {
    httpServer.on("request", handler);
    return httpServer;
  }});

  // WebSocket server for Twilio media streams
  const wss = new WebSocketServer({ server: httpServer, path: "/voice/stream" });

  wss.on("connection", (ws: WebSocket) => {
    console.log("[ws] New media stream connection");
    handleMediaStream(ws);
  });

  // Parse Twilio's application/x-www-form-urlencoded bodies
  app.addContentTypeParser(
    "application/x-www-form-urlencoded",
    function (_request, payload, done) {
      let body = "";
      payload.on("data", (chunk: Buffer) => { body += chunk.toString(); });
      payload.on("end", () => {
        const parsed = Object.fromEntries(new URLSearchParams(body));
        done(null, parsed);
      });
    }
  );

  // Health check
  app.get("/health", async () => ({ status: "ok", service: "jackie-voice" }));

  // Twilio webhook — called when someone dials Jackie's number
  app.all("/voice/webhook", async (request, reply) => {
    const streamUrl = publicUrl
      ? `${publicUrl.replace(/^http/, "ws")}/voice/stream`
      : `ws://localhost:${port}/voice/stream`;

    console.log(`[webhook] Incoming call — streaming to ${streamUrl}`);

    const twiml = `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="${streamUrl}">
      <Parameter name="caller" value="${escapeXml((request.body as Record<string, string>)?.From ?? "unknown")}" />
    </Stream>
  </Connect>
</Response>`;

    reply.type("text/xml").send(twiml);
  });

  // Outbound call — Jackie calls Lily (or a specified number)
  app.post("/voice/call", async (request, reply) => {
    // Auth check: require bearer token to prevent unauthorized calls
    const bearerToken = request.headers.authorization;
    if (!config.server.callApiSecret) {
      return reply.status(500).send({ error: "CALL_API_SECRET not configured" });
    }
    if (bearerToken !== `Bearer ${config.server.callApiSecret}`) {
      return reply.status(401).send({ error: "Unauthorized" });
    }

    const body = request.body as Record<string, string> | undefined;
    const to = body?.to ?? config.twilio.lilyPhoneNumber;

    if (!to) {
      return reply.status(400).send({ error: "No phone number provided and LILY_PHONE_NUMBER not set" });
    }

    if (!publicUrl) {
      return reply.status(500).send({ error: "PUBLIC_URL not set, Twilio cannot reach webhook" });
    }

    const { accountSid, authToken, phoneNumber } = config.twilio;
    const twilioUrl = `https://api.twilio.com/2010-04-01/Accounts/${accountSid}/Calls.json`;
    const authHeader = "Basic " + Buffer.from(`${accountSid}:${authToken}`).toString("base64");

    const params = new URLSearchParams({
      To: to,
      From: phoneNumber,
      Url: `${publicUrl}/voice/webhook`,
      StatusCallback: `${publicUrl}/voice/status`,
    });

    console.log(`[outbound] Calling ${to} from ${phoneNumber}`);

    const resp = await fetch(twilioUrl, {
      method: "POST",
      headers: {
        Authorization: authHeader,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: params.toString(),
    });

    const result = await resp.json();

    if (!resp.ok) {
      console.error("[outbound] Twilio error:", result);
      return reply.status(resp.status).send({ error: "Twilio call failed", details: result });
    }

    console.log(`[outbound] Call initiated — SID: ${(result as Record<string, string>).sid}`);
    return { ok: true, callSid: (result as Record<string, string>).sid };
  });

  // Twilio status callback (optional, for logging)
  app.post("/voice/status", async (request) => {
    const body = request.body as Record<string, string>;
    console.log(
      `[status] Call ${body?.CallSid} — ${body?.CallStatus} (duration: ${body?.CallDuration ?? "?"}s)`
    );
    return { ok: true };
  });

  await app.ready();

  httpServer.listen(port, "0.0.0.0", () => {
    console.log(`Jackie Voice Service listening on port ${port}`);
    if (publicUrl) {
      console.log(`Public URL: ${publicUrl}`);
      console.log(`Twilio webhook: POST ${publicUrl}/voice/webhook`);
    } else {
      console.log(
        "WARNING: No PUBLIC_URL set — Twilio won't be able to reach this server"
      );
    }
  });
}
