import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef, MouseEvent } from "react";

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
//
// Disabled is handled via ARIA rather than the native `disabled` attribute:
// browsers ignore the CSS `cursor` and suppress `:hover` on natively-disabled
// buttons, so a blocked cursor + dulled look can never show. Instead we add the
// `.disabled` class (which the `.button.disabled` rules style), mark it
// `aria-disabled`, pull it out of the tab order, and no-op the click.
export default function Button({ children, variant = "grey", small, className, disabled, onClick, ...rest }: Props) {
  const classes = [VARIANT_CLASS[variant], small ? "small" : "", disabled ? "disabled" : "", className ?? ""]
    .filter(Boolean)
    .join(" ");
  const handleClick = (e: MouseEvent<HTMLButtonElement>) => {
    if (disabled) {
      e.preventDefault();
      return;
    }
    onClick?.(e);
  };
  return (
    <button
      className={classes}
      aria-disabled={disabled || undefined}
      tabIndex={disabled ? -1 : undefined}
      onClick={handleClick}
      {...rest}
    >
      {children}
    </button>
  );
}
