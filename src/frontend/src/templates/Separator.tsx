import type { CSSProperties } from "react";

interface Props {
  color?: CSSProperties["color"];
}

export default function Separator({ color }: Props) {
  const name =`separator ${color}`
  const dynamicStyle: CSSProperties = {
    color: color ?? "inherit",
  };
  return <>
    <span className={name} style={dynamicStyle}>|</span>
  </>
}