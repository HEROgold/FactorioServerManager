import { useState } from "react";


export function SubmitButton({ busy, idle }: { busy: string; idle: string }) {
  const [isSubmitting, setIsSubmitting] = useState(false)

  return <>
  <div className="text-right">
    <button
      type="submit"
      className="button-green-right"
      disabled={isSubmitting}
      onClick={() => setIsSubmitting(true)}
    >
      {isSubmitting ? busy : idle}
    </button>
  </div>
  </>;
}
