type Tone = "green" | "red" | "blue" | "grey";

interface Props {
  status: string | null | undefined;
  /** Show the status text beside the light. */
  showLabel?: boolean;
}

// Maps a backend server status (created/running/restarting/exited/paused/dead/
// unknown) to a Factorio control-panel style coloured light.
function toneFor(status: string | null | undefined): { tone: Tone; pulse: boolean } {
  switch ((status ?? "").toLowerCase()) {
    case "running":
      return { tone: "green", pulse: false };
    case "exited":
    case "dead":
      return { tone: "red", pulse: false };
    case "paused":
      return { tone: "blue", pulse: false };
    // "starting"/"stopping" are synthetic, optimistic states shown while a
    // start/stop/restart action is in flight.
    case "restarting":
    case "starting":
    case "stopping":
    case "created":
      return { tone: "blue", pulse: true };
    default:
      return { tone: "grey", pulse: false };
  }
}

export default function StatusLight({ status, showLabel = false }: Props) {
  const { tone, pulse } = toneFor(status);
  const label = status || "unknown";
  const dot = (
    <span
      className={`status-light status-light-${tone}${pulse ? " status-light-pulse" : ""}`}
      role="img"
      aria-label={`Status: ${label}`}
      title={label}
    />
  );

  if (!showLabel) {
    return dot;
  }

  return (
    <span className="status-indicator">
      {dot}
      <span className="status-indicator-label">{label}</span>
    </span>
  );
}
