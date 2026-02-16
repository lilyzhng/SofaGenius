/** Base URL for API requests. Empty in dev (Vite proxy), Railway URL in production. */
export const API_BASE = import.meta.env.VITE_API_URL || "";
