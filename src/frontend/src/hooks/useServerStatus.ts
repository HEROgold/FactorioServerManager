import { useEffect, useState } from "react";
import { apiUrl } from "@/api";

// Subscribes to the backend status SSE stream and returns the live server
// status string. Reused by the server-detail header and the Manage tab.
export function useServerStatus(name: string, initial?: string | null): string {
  const [status, setStatus] = useState<string>(initial ?? "unknown");

  useEffect(() => {
    const es = new EventSource(apiUrl(`/api/server/${name}/status`), {
      withCredentials: true,
    });
    const onUpdate = (event: MessageEvent) => setStatus(event.data);
    es.addEventListener("serverStatusUpdate", onUpdate);
    es.onmessage = onUpdate;
    // Don't close on error: let EventSource auto-reconnect after a transient
    // failure, otherwise the status light freezes permanently.

    return () => {
      es.removeEventListener("serverStatusUpdate", onUpdate);
      es.close();
    };
  }, [name]);

  return status;
}
