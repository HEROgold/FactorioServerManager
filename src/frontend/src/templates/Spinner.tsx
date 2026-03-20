enum Size {
  xs,
  sm,
  md,
  lg,
  xl
}

interface Props {
  size?: Size;
}

export default function Spinner({ size = Size.md }: Props) {
  return <>
    <span className={`loading loading-spinner loading-${size.toString()}`}></span>
  </>
}
