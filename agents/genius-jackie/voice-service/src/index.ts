import { startServer } from "./webhook.js";

console.log("Starting Jackie Voice Service...");
startServer().catch((err) => {
  console.error("Failed to start:", err);
  process.exit(1);
});
