import type { ReactNode } from "react";

type ContainerType = "inner"

interface Props {
  children: ReactNode;
  type?: ContainerType;
}

export default function Container({ children, type = "inner" }: Props) {
  return <>
    <div className={`container container-${type.toString()}`}>{children}</div>
  </>
}
