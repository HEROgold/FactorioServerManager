import { useEffect, useState } from "react";
import { getJSON } from "@/api";
import Light, { type Tone } from "./Light";

interface Reachability {
  discoverable: boolean | null;
  reason: string | null;
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

  let tone: Tone = "grey";
  let label = "Unknown";
  let title = state?.reason ?? "Reachability unknown";

  if (checking && !state) {
    title = "Checking public reachability…";
    label = "Checking…";
  } else if (state?.discoverable === true) {
    tone = "green";
    label = "Discoverable";
    title = state.reason ?? "Listed in the public game browser";
  } else if (state?.discoverable === false) {
    tone = "orange";
    label = "Not discoverable";
    title = state.reason ?? "Not publicly reachable";
  }

  return <Light tone={tone} label={label} title={title} />;
}
