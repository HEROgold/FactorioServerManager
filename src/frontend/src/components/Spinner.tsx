export enum Size {
  xs = "xs",
  sm = "sm",
  md = "md",
  lg = "lg",
  xl = "xl",
}

interface Props {
  size?: Size;
}

// Factorio-themed spinner (replaces the old DaisyUI `loading-spinner`).
// Styled via `.spinner` / `.spinner-{size}` in main.css.
export default function Spinner({ size = Size.md }: Props) {
  return <span className={`spinner spinner-${size}`} role="status" aria-label="Loading" />;
}
