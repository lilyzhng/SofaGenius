import { config as loadEnv } from "dotenv";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

// Load .env from the voice-service directory or Jackie's directory
loadEnv({ path: resolve(__dirname, "../.env") });
loadEnv({ path: resolve(process.env.JACKIE_DIR ?? "", ".env") });

function required(key: string): string {
  const val = process.env[key];
  if (!val) throw new Error(`Missing required env var: ${key}`);
  return val;
}

export const config = {
  twilio: {
    accountSid: required("TWILIO_ACCOUNT_SID"),
    authToken: required("TWILIO_AUTH_TOKEN"),
    phoneNumber: required("TWILIO_PHONE_NUMBER"),
  },
  openai: {
    apiKey: required("OPENAI_API_KEY"),
  },
  server: {
    port: parseInt(process.env.PORT ?? "3334", 10),
    publicUrl: process.env.PUBLIC_URL ?? "",
  },
  jackie: {
    dir: process.env.JACKIE_DIR ?? "/home/node/SofaGenius/agents/genius-product",
    memoryDir:
      process.env.JACKIE_MEMORY_DIR ?? "/home/node/lily-memory/Agents/jackie_product",
    skillsDir:
      process.env.JACKIE_SKILLS_DIR ?? "/home/node/SofaGenius/agents/genius-product/skills",
  },
} as const;
