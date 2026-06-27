import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef } from "react";

interface Props extends Children, ComponentPropsWithoutRef<"pre"> {}

// Barebones, style-free preformatted-text tag. TODO: port `.log-window` styling (commented).
export default function Pre({ children, ...rest }: Props) {
  return <pre {...rest}>{children}</pre>;
}
