import type { ComponentPropsWithoutRef } from "react";

interface Props extends ComponentPropsWithoutRef<"input"> {
  wrapperClassName?: string;
}

export default function SearchInput({ wrapperClassName = "", ...rest }: Props) {
  const wrapperCls = ["mod-search-form", wrapperClassName].filter(Boolean).join(" ");
  return (
    <form className={wrapperCls} onSubmit={(e) => e.preventDefault()}>
      <input type="search" {...rest} />
    </form>
  );
}
