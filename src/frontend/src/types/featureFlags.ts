// Feature flags mirror the backend `FeatureFlags` class (see src/api/config.py).
// Nested groups (e.g. Mods) map to nested objects; the backend serves this shape
// from GET /api/feature-flags and signals changes over /api/feature-flags/stream.

export interface FeatureFlags {
  rcon_console: boolean;
  server_create: boolean;
  Mods: {
    enabled: boolean;
    manage: boolean;
    download: boolean;
  };
}

// Safe defaults used until the backend responds. A gated (dark-launch) feature
// defaults OFF so it stays hidden if the fetch fails; existing features default
// ON so their behavior is unchanged.
export const DEFAULT_FLAGS: FeatureFlags = {
  rcon_console: true,
  server_create: true,
  Mods: {
    enabled: false,
    manage: true,
    download: true,
  },
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

// Deep-merge a (possibly partial or malformed) backend payload over `defaults`,
// keeping only keys the defaults define. Unknown keys are ignored and missing
// keys keep their default, so the returned object always matches FeatureFlags.
function merge<T>(defaults: T, payload: unknown): T {
  if (!isRecord(payload)) {
    return defaults;
  }
  if (!isRecord(defaults)) {
    return defaults;
  }
  const out: Record<string, unknown> = { ...defaults };
  for (const key of Object.keys(defaults)) {
    const dflt = (defaults as Record<string, unknown>)[key];
    const incoming = payload[key];
    if (incoming === undefined) {
      continue;
    }
    out[key] = isRecord(dflt) ? merge(dflt, incoming) : (typeof incoming === typeof dflt ? incoming : dflt);
  }
  return out as T;
}

/** Merge a backend payload over DEFAULT_FLAGS, guaranteeing a valid FeatureFlags. */
export function mergeFlags(payload: unknown): FeatureFlags {
  return merge(DEFAULT_FLAGS, payload);
}
