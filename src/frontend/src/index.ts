import { serve } from "bun";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import index from "./index.html";

// In development the SPA is served by Bun while the API runs as a separate
// FastAPI process. Proxy every `/api/*` request to the backend so the browser
// talks to a single origin (keeps cookies and SSE working without CORS).
//
// The backend binds a random free port and writes it to `.fsm-backend-port` at
// the repo root, so resolve the target per request: `API_TARGET` (Docker) wins,
// then the published port, then a sensible default.
const PORT_FILE = join(import.meta.dir, "..", "..", "..", ".fsm-backend-port");

function apiTarget(): string {
  if (process.env.API_TARGET) return process.env.API_TARGET;
  try {
    const port = readFileSync(PORT_FILE, "utf8").trim();
    if (port) return `http://127.0.0.1:${port}`;
  } catch {
    // Backend hasn't published its port yet — fall through to the default.
  }
  return "http://127.0.0.1:8000";
}

async function proxyApi(req: Request): Promise<Response> {
  const API_TARGET = apiTarget();
  const url = new URL(req.url);
  const target = API_TARGET + url.pathname + url.search;

  const headers = new Headers(req.headers);
  headers.delete("host");

  const init: RequestInit = {
    method: req.method,
    headers,
    redirect: "manual",
  };
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.arrayBuffer();
  }

  try {
    return await fetch(target, init);
  } catch (err) {
    return Response.json(
      { detail: `Unable to reach API backend at ${API_TARGET}` },
      { status: 502 },
    );
  }
}

const server = serve({
  routes: {
    // Forward API calls to the FastAPI backend.
    "/api/*": proxyApi,

    // Serve index.html for all other (SPA) routes.
    "/*": index,
  },

  development: process.env.NODE_ENV !== "production" && {
    // Enable browser hot reloading in development
    hmr: true,

    // Echo console logs from the browser to the server
    console: true,
  },
});

console.log(`🚀 Server running at ${server.url}`);
console.log(`🔌 Proxying /api -> ${apiTarget()}`);
