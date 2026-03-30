import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef } from "react";

interface Props extends Children, ComponentPropsWithoutRef<"button"> {}

export default function ButtonGhost({ children, className = "", ...rest }: Props) {
  const cls = ["button-ghost", className].filter(Boolean).join(" ");
  return (
    <button {...rest} className={cls}>
      {children}
    </button>
  );
}
