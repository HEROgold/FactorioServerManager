export function SubmitButton({ isSubmitting }: { isSubmitting: boolean; }) {
  return <><div className="text-right">
    <button
      type="submit"
      className="button-green-right"
      disabled={isSubmitting}
    >
      {isSubmitting ? "Logging in..." : "Log in"}
    </button>
  </div>
  </>;
}
