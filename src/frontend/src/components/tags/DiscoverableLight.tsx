import { useEffect, useState } from "react";
import { getJSON } from "@/api";

interface Reachability {
  discoverable: boolean | null;
  reason: string | null;
}

type Tone = "green" | "orange" | "grey";

function Indicator({ tone, label, title }: { tone: Tone; label: string; title: string }) {
  return (
    <span className="status-indicator">
      <span className={`status-light status-light-${tone}`} role="img" aria-label={title} title={title} />
      <span className="status-indicator-label">{label}</span>
    </span>
  );
}

// Reports whether the server is *actually* publicly discoverable by asking the
// backend, which checks Factorio's public matchmaking list. Re-checks
// periodically while mounted (the listing changes as the server starts/stops).
export default function DiscoverableLight({ name }: { name: string }) {
  const [state, setState] = useState<Reachability | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    let active = true;
    setChecking(true);
    setState(null);

    const check = async () => {
      try {
        const result = await getJSON<Reachability>(`/api/server/${name}/reachable`);
        if (active) setState(result);
      } catch {
        if (active) setState({ discoverable: null, reason: "Reachability check failed" });
      } finally {
        if (active) setChecking(false);
      }
    };

    void check();
    const id = window.setInterval(check, 60_000);
    return () => {
      active = false;
      window.clearInterval(id);
    };
  }, [name]);

  if (checking && !state) {
    return <Indicator tone="grey" label="Checking…" title="Checking public reachability…" />;
  }

  const discoverable = state?.discoverable;
  if (discoverable === true) {
    return <Indicator tone="green" label="Discoverable" title={state?.reason ?? "Listed in the public game browser"} />;
  }
  if (discoverable === false) {
    return <Indicator tone="orange" label="Not discoverable" title={state?.reason ?? "Not publicly reachable"} />;
  }
  return <Indicator tone="grey" label="Unknown" title={state?.reason ?? "Reachability unknown"} />;
}
