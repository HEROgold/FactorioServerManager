import { useEffect, useRef, useState } from "react";
import type { Dispatch, MutableRefObject, SetStateAction } from "react";
import { apiUrl, getJSON } from "@/api";
import Button from "@/components/tags/Button";

interface LogsResponse {
  current_log: string;
  previous_log: string;
}

interface Props {
  name: string;
  // Buffer lives in the parent so "Clear" survives tab switches.
  lines: string[];
  setLines: Dispatch<SetStateAction<string[]>>;
  cleared: boolean;
  setCleared: (value: boolean) => void;
  seededRef: MutableRefObject<boolean>;
}

const MAX_LINES = 5000;

function splitLog(text: string): string[] {
  return text.replace(/\n$/, "").split("\n");
}

// Live log feed. The buffer + "cleared" flag are owned by ServerDetail so they
// persist across tab switches; this component seeds the backlog once, streams
// new lines, and offers Clear / Restore.
export default function LogsTab({ name, lines, setLines, cleared, setCleared, seededRef }: Props) {
  const [paused, setPaused] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pausedRef = useRef(false);
  const windowRef = useRef<HTMLDivElement | null>(null);
  pausedRef.current = paused;

  // Seed the backlog exactly once per server, and never after a manual clear.
  useEffect(() => {
    if (cleared || seededRef.current) return;
    seededRef.current = true;
    let active = true;
    (async () => {
      try {
        const data = await getJSON<LogsResponse>(`/api/server/${name}/logs`);
        if (active && data.current_log) {
          setLines(splitLog(data.current_log));
        }
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Failed to load logs");
      }
    })();
    return () => {
      active = false;
    };
  }, [name, cleared, seededRef, setLines]);

  // Live stream.
  useEffect(() => {
    const es = new EventSource(apiUrl(`/api/server/${name}/logs/stream`), {
      withCredentials: true,
    });
    es.onmessage = (event) => {
      if (pausedRef.current) return;
      setLines((prev) => {
        const next = prev.concat(String(event.data).split("\n"));
        return next.length > MAX_LINES ? next.slice(next.length - MAX_LINES) : next;
      });
    };
    // Browser auto-reconnects on error; don't close so the feed resumes.
    return () => es.close();
  }, [name, setLines]);

  // Auto-scroll to the newest line unless paused.
  useEffect(() => {
    if (paused) return;
    const el = windowRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [lines, paused]);

  const handleClear = () => {
    setLines([]);
    setCleared(true);
  };

  const handleRestore = async () => {
    setError(null);
    try {
      const data = await getJSON<LogsResponse>(`/api/server/${name}/logs`);
      setLines(data.current_log ? splitLog(data.current_log) : []);
      seededRef.current = true;
      setCleared(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load logs");
    }
  };

  return (
    <div className="panel-inset-lighter">
      <div className="flex flex-space-between flex-items-center mb12" style={{ gap: 12, flexWrap: "wrap" }}>
        <h3 className="mt0 mb0">Live Logs</h3>
        <div className="flex" style={{ gap: 8 }}>
          <Button variant="ghost" small onClick={() => setPaused((p) => !p)}>
            {paused ? "Resume" : "Pause"}
          </Button>
          <Button variant="ghost" small onClick={handleClear}>Clear</Button>
          <Button variant="ghost" small onClick={handleRestore}>Restore all</Button>
        </div>
      </div>
      {error ? <p className="red">{error}</p> : null}
      <div className="log-window" ref={windowRef}>
        {lines.length ? lines.join("\n") : cleared ? "Logs cleared. New output will appear here; use “Restore all” to reload history." : "Waiting for log output…"}
      </div>
    </div>
  );
}
