import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef } from "react";

type Variant = "grey" | "green" | "red" | "ghost";

interface Props extends Children, ComponentPropsWithoutRef<"button"> {
  /** Factorio button colour. Defaults to the grey `.button`. */
  variant?: Variant;
  /** Render the compact `.button.small` variant. */
  small?: boolean;
}

const VARIANT_CLASS: Record<Variant, string> = {
  grey: "button",
  green: "button button-green",
  red: "button button-red",
  ghost: "button button-ghost",
};

// Self-styling Factorio button. Always carries the `.button` class so callers
// can't accidentally bleed a default browser button; extra `className` is
// merged on top for one-off tweaks.
export default function Button({ children, variant = "grey", small, className, ...rest }: Props) {
  const classes = [VARIANT_CLASS[variant], small ? "small" : "", className ?? ""]
    .filter(Boolean)
    .join(" ");
  return (
    <button className={classes} {...rest}>
      {children}
    </button>
  );
}
