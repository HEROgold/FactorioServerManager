import { Link } from "react-router-dom";
// eslint-disable-next-line import/no-unresolved -- resolved to a URL by Bun's bundler (see bun-env.d.ts)
import favicon from "@/favicon.svg";

// Placeholder wordmark (no Factorio/Wube logo assets) until a real mark is
// designed. The cog icon matches favicon.svg so the browser tab and header
// read as the same identity for now.
export function Logo() {
  return (
    <Link to="/servers" className="brand-mark">
      <img src={favicon} alt="" width={40} height={40} className="brand-mark-icon" />
      <span className="brand-mark-text">Factorio Server Manager</span>
    </Link>
  );
}
