import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef } from "react";

interface Props extends Children, ComponentPropsWithoutRef<"fieldset"> {}

// Barebones, style-free fieldset tag. TODO: port fieldset styling (commented).
export default function Fieldset({ children, ...rest }: Props) {
  return <fieldset {...rest}>{children}</fieldset>;
}
