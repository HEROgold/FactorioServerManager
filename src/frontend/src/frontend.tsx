/**
 * This file is the entry point for the React app, it sets up the root
 * element and renders the App component to the DOM.
 *
 * It is included in `src/index.html`.
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import * as Sentry from "@sentry/react";
import { App } from "./App";

Sentry.init({
  dsn:
    (typeof Bun !== "undefined" && (Bun as any).env?.SENTRY_DSN) ??
    (import.meta as any).env?.SENTRY_DSN ??
    (import.meta as any).env?.SENTRY_DSN,
  // Keep PII out of Sentry: avoid collecting IPs and, more importantly, any
  // login credentials that could be captured in breadcrumbs or session replays.
  sendDefaultPii: false,
});

const elem = document.getElementById("root")!;
const app = (
  <StrictMode>
    <App />
  </StrictMode>
);

if (import.meta.hot) {
  // With hot module reloading, `import.meta.hot.data` is persisted.
  const root = (import.meta.hot.data.root ??= createRoot(elem));
  root.render(app);
} else {
  // The hot module reloading API is not available in production.
  createRoot(elem).render(app);
}
