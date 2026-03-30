import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef, CSSProperties } from "react";

interface Props extends Children, ComponentPropsWithoutRef<"input"> { }

const baseInputStyle: CSSProperties = {
  verticalAlign: "baseline",
  fontFamily: "inherit",
  lineHeight: 1.2,
  fontSize: "105%",
  height: 36,
  maxWidth: "100%",
  background: "#8e8e8e",
  borderRadius: 4,
  padding: 6,
  border: "none",
  boxShadow: [
    "inset 0px 4px 1px -2px #000",
    "inset 0px -4px 1px -2px #c5c5c5",
    "inset 2px 0px 1px 0px #5f5f5f",
    "inset -2px 0px 1px 0px #5f5f5f",
    "inset 0px -2px 2px 0px #5f5f5f",
    "0px 0px 4px 1px #2e2521",
  ].join(", "),
};

const focusInputStyle: CSSProperties = {
  outline: "none",
  background: "#f0dab4",
  boxShadow: [
    "inset 0px 4px 2px -2px #000",
    "inset 0px -1px 1px 0px #74624b",
    "inset 0px -4px 2px -2px #e0e0e0",
    "inset 2px 0px 2px 0px #a6885c",
    "inset -2px 0px 2px 0px #a6885c",
    "0px 0px 4px 1px #2e2521",
  ].join(", "),
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
