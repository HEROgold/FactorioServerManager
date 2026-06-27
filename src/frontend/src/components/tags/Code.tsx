import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef } from "react";

interface Props extends Children, ComponentPropsWithoutRef<"code"> {}

// Barebones, style-free inline-code tag. TODO: port code styling (commented).
export default function Code({ children, ...rest }: Props) {
  return <code {...rest}>{children}</code>;
}
