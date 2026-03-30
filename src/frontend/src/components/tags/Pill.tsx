import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef, CSSProperties } from "react";

interface Props extends Children, ComponentPropsWithoutRef<"span"> {
  variant?: "active" | "inactive" | "warning" | "outline";
}

const baseStyle: CSSProperties = {
  padding: "4px 10px",
  borderRadius: "999px",
  fontSize: "0.75rem",
  textTransform: "uppercase",
  letterSpacing: "0.1em",
  border: "1px solid rgba(255,255,255,0.2)",
  display: "inline-block",
};

const variantStyles: Record<NonNullable<Props["variant"]>, CSSProperties> = {
  active: {
    borderColor: "rgba(116, 225, 143, 0.7)",
    color: "#aee7be",
  },
  inactive: {
    borderColor: "rgba(255, 255, 255, 0.2)",
    color: "rgba(255, 255, 255, 0.6)",
  },
  warning: {
    borderColor: "rgba(255, 117, 85, 0.9)",
    color: "#ff8b6a",
  },
  outline: {
    borderColor: "rgba(122, 207, 221, 0.4)",
    color: "#7dcaed",
  },
};

export default function Pill({ children, variant = "inactive", style, ...rest }: Props) {
  const combined: CSSProperties = {
    ...baseStyle,
    ...(variant ? variantStyles[variant] : {}),
    ...(style as CSSProperties),
  };

  return (
    <span {...rest} style={combined}>
      {children}
    </span>
  );
}
