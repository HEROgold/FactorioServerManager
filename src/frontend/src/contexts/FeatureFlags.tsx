import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import * as Sentry from "@sentry/react";

import { apiFetch, apiUrl } from "@/api";
import { DEFAULT_FLAGS, mergeFlags, type FeatureFlags } from "@/types/featureFlags";

/**
 * Report evaluated flags to Sentry so they're attached to any subsequent error
 * event (the "Feature Flags" section). Flattens nested groups to dotted keys,
 * mirroring the backend (e.g. `Mods.enabled`). Booleans only, per the SDK.
 */
function recordFlagEvaluations(flags: FeatureFlags): void {
  const integration = Sentry.getClient()?.getIntegrationByName<Sentry.FeatureFlagsIntegration>(
    "FeatureFlags",
  );
  if (!integration) {
    return;
  }
  const walk = (obj: Record<string, unknown>, prefix: string) => {
    for (const [name, value] of Object.entries(obj)) {
      const key = `${prefix}${name}`;
      if (typeof value === "boolean") {
        integration.addFeatureFlag(key, value);
      } else if (value && typeof value === "object") {
        walk(value as Record<string, unknown>, `${key}.`);
      }
    }
  };
  walk(flags as unknown as Record<string, unknown>, "");
}

interface FeatureFlagsContextValue {
  flags: FeatureFlags;
  loading: boolean;
}

const defaultValue: FeatureFlagsContextValue = {
  flags: DEFAULT_FLAGS,
  loading: true,
};

const FeatureFlagsContext = createContext<FeatureFlagsContextValue>(defaultValue);

export function FeatureFlagsProvider({ children }: { children: React.ReactNode }) {
  const [flags, setFlags] = useState<FeatureFlags>(DEFAULT_FLAGS);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    try {
      const res = await apiFetch("/api/feature-flags");
      if (res.ok) {
        const next = mergeFlags(await res.json());
        setFlags(next);
        recordFlagEvaluations(next);
      }
    } catch {
      // Keep the current flags on a transient failure.
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // If the server injected a global `__FLAGS__`, trust it first (same pattern
    // as `window.__USER__`); otherwise fetch the current values.
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    const injected = typeof window !== "undefined" ? window.__FLAGS__ : undefined;
    if (injected) {
      const merged = mergeFlags(injected);
      setFlags(merged);
      recordFlagEvaluations(merged);
      setLoading(false);
    } else {
      void refetch();
    }

    // Live-reload: the backend pings this SSE stream whenever a flag changes in
    // api_config.ini, so we re-fetch without a restart or page reload. Don't
    // close on error — let EventSource auto-reconnect after a transient failure.
    const es = new EventSource(apiUrl("/api/feature-flags/stream"), { withCredentials: true });
    const onUpdate = () => void refetch();
    es.addEventListener("featureFlagsUpdate", onUpdate);

    return () => {
      es.removeEventListener("featureFlagsUpdate", onUpdate);
      es.close();
    };
  }, [refetch]);

  return (
    <FeatureFlagsContext.Provider value={{ flags, loading }}>
      {children}
    </FeatureFlagsContext.Provider>
  );
}

export function useFeatureFlags() {
  return useContext(FeatureFlagsContext);
}

/**
 * Route guard: renders `children` only when `when(flags)` holds, otherwise
 * redirects to `fallback`. Uses a predicate so nested flags stay first-class,
 * e.g. `<FlagGate when={f => f.Mods.enabled}>`.
 */
export function FlagGate({
  when,
  children,
  fallback = "/servers",
}: {
  when: (flags: FeatureFlags) => boolean;
  children: React.ReactNode;
  fallback?: string;
}) {
  const { flags, loading } = useFeatureFlags();
  if (loading) {
    return null;
  }
  return when(flags) ? <>{children}</> : <Navigate to={fallback} replace />;
}

export default FeatureFlagsContext;
