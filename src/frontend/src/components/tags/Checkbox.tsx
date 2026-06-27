import type { ComponentPropsWithoutRef, ReactNode } from "react";

interface Props extends ComponentPropsWithoutRef<"input"> {
  /** Text/markup shown beside the checkbox. */
  label?: ReactNode;
  /** Extra classes for the wrapping label. */
  labelClassName?: string;
}

// Factorio checkbox. Renders the themed `.checkbox-label` / `.checkbox` pattern
// from main.css (a hidden native input + a styled box), replacing the default
// browser checkmark. `type` is fixed to "checkbox".
export default function Checkbox({ label, labelClassName, ...rest }: Props) {
  const classes = ["checkbox-label", labelClassName ?? ""].filter(Boolean).join(" ");
  return (
    <label className={classes}>
      <input type="checkbox" {...rest} />
      <span className="checkbox" />
      {label != null ? <div>{label}</div> : null}
    </label>
  );
}
