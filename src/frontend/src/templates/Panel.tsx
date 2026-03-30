import type { Children } from "@/interfaces/children";
import type { ComponentPropsWithoutRef } from "react";

type PanelType = "inset-lighter"

interface Props extends Children, ComponentPropsWithoutRef<"div"> {
  type?: PanelType;
}

export default function Panel({ children, type, ...rest }: Props) {
  return <>
    <div
      className={type ? `panel-${type.toString()}` : "panel"}
      {...rest}
    >
      {children}
    </div>
  </>
}
