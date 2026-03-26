import { startServer } from "./webhook.js";

// Keep the process alive — never crash on unhandled errors
process.on("uncaughtException", (err) => {
  console.error("[fatal] Uncaught exception (keeping alive):", err.message);
});
process.on("unhandledRejection", (err) => {
  console.error("[fatal] Unhandled rejection (keeping alive):", err);
});

console.log("Starting Jackie Voice Service...");
startServer().catch((err) => {
  console.error("Failed to start:", err);
  process.exit(1);
});
