import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef } from "react";

interface Props extends Children, ComponentPropsWithoutRef<"div"> {
  show?: boolean;
}

export default function Toast({ children, show = false, className = "", ...rest }: Props) {
  const cls = ["mod-toast", show ? "show" : "", className].filter(Boolean).join(" ");
  return (
    <div {...rest} className={cls}>
      {children}
    </div>
  );
}
