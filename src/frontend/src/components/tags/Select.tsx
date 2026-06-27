import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef } from "react";

interface Props extends Children, ComponentPropsWithoutRef<"select"> {}

// Self-styling Factorio select. Always carries `.button` (matched by the
// `select.button` rule in main.css) so it never falls back to a default
// browser dropdown; extra `className` is merged on top.
export default function Select({ children, className, ...rest }: Props) {
  const classes = ["button", className ?? ""].filter(Boolean).join(" ");
  return (
    <select className={classes} {...rest}>
      {children}
    </select>
  );
}
