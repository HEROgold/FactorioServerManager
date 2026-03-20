import type { Children } from "@/interfaces/children";
import type { ReactNode } from "react";

type PanelType = "inset-lighter"

interface Props extends Children {
  type?: PanelType;
}

export default function Panel({ children, type }: Props) {
  return <>
    <div className=
      {type ? `panel-${type.toString()}` : "panel"}
    >
      {children}
    </div>
  </>
}
