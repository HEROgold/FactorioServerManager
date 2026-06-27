import Light, { type Tone } from "./Light";

interface Props {
  /** true = listed publicly, false = not listed, null/undefined = unknown. */
  reachable: boolean | null | undefined;
  showLabel?: boolean;
}

// Renders a discoverability dot from an already-known reachability value (no
// fetching) — used in list rows. DiscoverableLight is the self-fetching variant.
export default function ReachabilityLight({ reachable, showLabel = false }: Props) {
  let tone: Tone = "grey";
  let label = "Unknown";
  let title = "Discoverability unknown";

  if (reachable === true) {
    tone = "green";
    label = "Discoverable";
    title = "Listed in the public game browser";
  } else if (reachable === false) {
    tone = "orange";
    label = "Not discoverable";
    title = "Not listed in the public game browser";
  }

  return <Light tone={tone} label={showLabel ? label : undefined} title={title} />;
}
