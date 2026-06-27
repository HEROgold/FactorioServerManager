import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef } from "react";

interface Props extends Children, ComponentPropsWithoutRef<"section"> {}

// Barebones, style-free section tag. TODO: port section styling (commented).
export default function Section({ children, ...rest }: Props) {
  return <section {...rest}>{children}</section>;
}
