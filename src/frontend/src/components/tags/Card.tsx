import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef } from "react";

interface Props extends Children, ComponentPropsWithoutRef<"div"> {
  variant?: "default" | "detail";
}

export default function Card({ children, className = "", variant = "default", ...rest }: Props) {
  const base = variant === "default" ? "mod-card" : "mod-detail-card";
  const cls = [base, className].filter(Boolean).join(" ");
  return (
    <div {...rest} className={cls}>
      {children}
    </div>
  );
}
