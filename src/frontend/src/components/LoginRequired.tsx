// Friendly stand-in shown when a protected request returns 401, instead of a
// raw "failed: 401" error. Links to /login and returns the user afterwards.
export default function LoginRequired({ message }: { message?: string }) {
  const next =
    typeof window !== "undefined" ? window.location.pathname + window.location.search : "/servers";
  const href = `/login?next=${encodeURIComponent(next)}`;

  return (
    <div className="panel-inset-lighter">
      <h3 className="mt0">Please log in</h3>
      <p>{message ?? "You need to be logged in to view this."}</p>
      <a className="button button-green" href={href}>Log in</a>
    </div>
  );
}
