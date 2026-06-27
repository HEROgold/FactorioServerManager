import { serve } from "bun";
import index from "./index.html";

// In development the SPA is served by Bun while the API runs as a separate
// FastAPI process. Proxy every `/api/*` request to the backend so the browser
// talks to a single origin (keeps cookies and SSE working without CORS).
const API_TARGET = process.env.API_TARGET ?? "http://127.0.0.1:8000";

async function proxyApi(req: Request): Promise<Response> {
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
console.log(`🔌 Proxying /api -> ${API_TARGET}`);
