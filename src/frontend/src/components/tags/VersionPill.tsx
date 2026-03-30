import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef } from "react";

interface Props extends Children, ComponentPropsWithoutRef<"span"> {}

export default function VersionPill({ children, className = "", ...rest }: Props) {
  const cls = ["mod-version-pill", className].filter(Boolean).join(" ");
  return (
    <span {...rest} className={cls}>
      {children}
    </span>
  );
}
