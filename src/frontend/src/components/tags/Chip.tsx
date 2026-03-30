import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef, CSSProperties } from "react";

interface Props extends Children, ComponentPropsWithoutRef<"span"> {}

const baseStyle: CSSProperties = {
  fontSize: "0.8rem",
  color: "rgba(255, 255, 255, 0.75)",
  display: "inline-block",
};

export default function Chip({ children, style, ...rest }: Props) {
  const combined: CSSProperties = {
    ...baseStyle,
    ...(style as CSSProperties),
  };

  return (
    <span {...rest} style={combined}>
      {children}
    </span>
  );
}
