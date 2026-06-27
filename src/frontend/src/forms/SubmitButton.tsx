export function SubmitButton({
  busy,
  idle,
  submitting = false,
}: {
  busy: string;
  idle: string;
  submitting?: boolean;
}) {
  return (
    <div className="text-right">
      <button type="submit" className="button-green-right" disabled={submitting}>
        {submitting ? busy : idle}
      </button>
    </div>
  );
}
