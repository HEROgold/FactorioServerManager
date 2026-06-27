import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "@/components/tags/Button";
import StatusLight from "@/components/tags/StatusLight";
import DiscoverableLight from "@/components/tags/DiscoverableLight";
import { apiFetch, sendJSON } from "@/api";

interface Props {
  name: string;
  ip: string;
  port: number;
  status: string;
  factorioVersion?: string | null;
}

type Action = "start" | "stop" | "restart";

// Optimistic label shown while an action is in flight.
const PENDING_STATUS: Record<Action, string> = {
  start: "starting",
  stop: "stopping",
  restart: "restarting",
};

export default function ManageTab({ name, ip, port, status, factorioVersion }: Props) {
  const navigate = useNavigate();
  const [pending, setPending] = useState<Action | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const isRunning = status === "running";
  const isStopped = status === "exited" || status === "dead";
  const busy = pending !== null;
  // While an action runs we show the optimistic state so the lamp reacts
  // immediately, before the backend/SSE confirms the real status.
  const displayStatus = pending ? PENDING_STATUS[pending] : status;

  const runAction = async (action: Action): Promise<void> => {
    setActionError(null);
    setPending(action);
    try {
      // The POST blocks until the backend finishes the docker operation, so
      // the buttons stay disabled until the server has actually
      // started/stopped/restarted (or the attempt failed).
      const res = await apiFetch(`/api/server/${name}/${action}`, { method: "POST" });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Failed to ${action} server`);
      }
    } catch (err) {
      setActionError(err instanceof Error ? err.message : `Failed to ${action} server`);
    } finally {
      setPending(null);
    }
  };

  const copyAddress = (): void => {
    navigator.clipboard.writeText(`${ip}:${port}`).catch((err) => console.error("Copy failed", err));
  };

  const handleDelete = async (): Promise<void> => {
    if (busy) return;
    if (!confirm(`Are you sure you want to delete ${name}? This cannot be undone.`)) {
      return;
    }
    try {
      await sendJSON(`/api/server/${name}`, "DELETE");
      navigate("/servers");
    } catch {
      alert("Delete failed");
    }
  };

  return (
    <div className="panel-inset-lighter">
      <h3 className="mt0">Status</h3>
      <div className="flex flex-wrap flex-items-center mb16" style={{ gap: 20 }}>
        <StatusLight status={displayStatus} showLabel />
        <DiscoverableLight name={name} />
      </div>

      <dl className="panel-hole mb16">
        <dt>Address</dt>
        <dd>{ip}:{port}</dd>
        <dt>Factorio version</dt>
        <dd>{factorioVersion || "Unknown"}</dd>
      </dl>

      <div className="button-group flex flex-wrap flex-items-center" style={{ gap: 8 }}>
        <Button variant="green" disabled={busy || isRunning} onClick={() => runAction("start")}>
          {pending === "start" ? "Starting…" : "Start"}
        </Button>
        <Button disabled={busy || isStopped} onClick={() => runAction("stop")}>
          {pending === "stop" ? "Stopping…" : "Stop"}
        </Button>
        <Button disabled={busy || !isRunning} onClick={() => runAction("restart")}>
          {pending === "restart" ? "Restarting…" : "Restart"}
        </Button>
        <Button variant="ghost" disabled={busy} onClick={copyAddress}>Copy {ip}:{port}</Button>
      </div>

      {actionError ? <p className="red mt8 mb0">{actionError}</p> : null}

      <hr />

      <Button variant="red" disabled={busy} onClick={handleDelete}>Delete Server</Button>
    </div>
  );
}
