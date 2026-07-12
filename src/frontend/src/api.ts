/**
 * Shared API client for talking to the FastAPI backend.
 *
 * In development the Bun dev server (see `index.ts`) proxies `/api/*` to the
 * backend, so the default base URL is empty (same origin). Set
 * `BUN_PUBLIC_API_URL` to target an absolute backend URL instead.
 */

const API_BASE: string =
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (import.meta as any).env?.BUN_PUBLIC_API_URL ?? "";

export function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

/** Error carrying the HTTP status so callers can branch (e.g. 401 -> login). */
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** True when an error is an unauthenticated (401) ApiError. */
export function isUnauthorized(err: unknown): boolean {
  return err instanceof ApiError && err.status === 401;
}

// Status codes whose backend `detail` is a curated, user-actionable validation
// message safe to show verbatim (e.g. "Server not found", "Command must not be
// empty"). Every other status — 401/403 (incl. CSRF), 5xx, unknown — is a
// security/infrastructure failure whose detail may leak internals, so it is
// replaced with GENERIC_ERROR. This is the single choke point that keeps such
// strings out of the UI even if the backend regresses.
const SAFE_DETAIL_STATUSES = new Set([400, 404, 409, 422, 429]);
const GENERIC_ERROR = "Something went wrong. Please try again.";

/** Pick the message shown to the user: backend detail only for safe validation
 * statuses, otherwise a neutral generic message. */
function userFacingMessage(status: number, detail?: unknown): string {
  if (SAFE_DETAIL_STATUSES.has(status) && typeof detail === "string" && detail.trim() !== "") {
    return detail;
  }
  return GENERIC_ERROR;
}

/** Name of the readable cookie holding the double-submit CSRF token. */
const CSRF_COOKIE = "fsm_csrf";

/** Read the current CSRF token from the (non-HttpOnly) session cookie, if any. */
function csrfToken(): string | undefined {
  const match = document.cookie.match(
    new RegExp(`(?:^|; )${CSRF_COOKIE}=([^;]*)`),
  );
  return match ? decodeURIComponent(match[1]) : undefined;
}

export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  return fetch(apiUrl(path), { credentials: "include", ...init });
}

export async function getJSON<T>(path: string): Promise<T> {
  const res = await apiFetch(path);
  if (!res.ok) {
    throw new ApiError(GENERIC_ERROR, res.status);
  }
  return (await res.json()) as T;
}

export async function sendJSON<T = unknown>(
  path: string,
  method: "POST" | "PATCH" | "PUT" | "DELETE",
  body?: unknown,
): Promise<T> {
  // Attach the double-submit CSRF token; the backend rejects cookie-authed
  // state changes whose X-CSRF-Token header does not match the fsm_csrf cookie.
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const token = csrfToken();
  if (token) headers["X-CSRF-Token"] = token;

  const res = await apiFetch(path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    let detail: unknown;
    try {
      detail = (await res.json())?.detail;
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new ApiError(userFacingMessage(res.status, detail), res.status);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}
