import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef, CSSProperties } from "react";

interface Props extends Children, ComponentPropsWithoutRef<"input"> { }

const baseInputStyle: CSSProperties = {
  verticalAlign: "baseline",
  fontFamily: "var(--font-sans)",
  lineHeight: 1.2,
  fontSize: "0.95rem",
  height: 38,
  maxWidth: "100%",
  background: "var(--color-panel-inset)",
  color: "var(--color-text-heading)",
  borderRadius: "var(--radius)",
  padding: "8px 10px",
  border: "1px solid var(--color-border-strong)",
  boxShadow: "inset 0px 1px 2px rgba(0, 0, 0, 0.5)",
};

export default function Input({ style, ...rest }: Props) {

  const combinedStyle: CSSProperties = {
    ...baseInputStyle,
    ...(style),
  };

  return <>
    <input
      {...rest}
      style={combinedStyle}
    >
    </input>
  </>
}
