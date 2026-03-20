import { useNavigation } from "react-router-dom";


export function SubmitButton() {
  const navigation = useNavigation()
  const isSubmitting = navigation.state === "submitting"

  return <>
  <div className="text-right">
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
