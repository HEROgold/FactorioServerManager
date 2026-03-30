import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef } from "react";

interface Props extends Children, ComponentPropsWithoutRef<"div"> {
  alert?: boolean;
}

export default function Placeholder({ children, alert = false, className = "", ...rest }: Props) {
  const cls = [alert ? "mod-alert" : "mod-placeholder", className].filter(Boolean).join(" ");
  return (
    <div {...rest} className={cls}>
      {children}
    </div>
  );
}
