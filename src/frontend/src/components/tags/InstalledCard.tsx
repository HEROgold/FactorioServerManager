import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef } from "react";

interface Props extends Children, ComponentPropsWithoutRef<"div"> {
  missing?: boolean;
}

export default function InstalledCard({ children, missing = false, className = "", ...rest }: Props) {
  const cls = ["mod-installed-card", missing ? "mod-installed-missing" : "", className].filter(Boolean).join(" ");
  return (
    <div {...rest} className={cls}>
      {children}
    </div>
  );
}
