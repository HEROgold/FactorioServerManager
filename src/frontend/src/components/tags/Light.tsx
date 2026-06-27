import type { ReactNode } from "react";

export type Tone = "green" | "red" | "blue" | "orange" | "grey";

interface Props {
  tone: Tone;
  /** Slowly pulse the dot (used for transient/in-flight states). */
  pulse?: boolean;
  /** Optional text shown beside the dot; omit for a bare dot. */
  label?: ReactNode;
  /** Accessible name / tooltip for the dot. */
  title: string;
}

// Single source of truth for the Factorio control-panel "light" markup: a
// coloured glowing dot, optionally followed by a label. StatusLight and
// DiscoverableLight are thin mappers on top of this.
export default function Light({ tone, pulse = false, label, title }: Props) {
  const dot = (
    <span
      className={`status-light status-light-${tone}${pulse ? " status-light-pulse" : ""}`}
      role="img"
      aria-label={title}
      title={title}
    />
  );

  if (label == null) {
    return dot;
  }

  return (
    <span className="status-indicator">
      {dot}
      <span className="status-indicator-label">{label}</span>
    </span>
  );
}
