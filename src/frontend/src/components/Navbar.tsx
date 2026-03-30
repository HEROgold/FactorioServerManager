import type { User } from "@/contexts/UserContext";
import Separator from "./Separator";

interface Props {
  user: User
}

/**
 * View for when user is already logged in
 */
function LoggedInView({ user }: Props) {
  return <>
    <a href="/servers">{user.display_name}</a>
    <Separator color={"#7dcaed"} />
    <a href="/logout">Log out</a>
  </>
}

/**
 * View for when a user still has to log in
 */
function HasToLogInView() {
  return <a href="/login">Log in</a>
}

export default function Navbar({ user }: { user: User | null }) {
  const LoginView = user?.authenticated ? <LoggedInView user={user} /> : <HasToLogInView />

  return <>
    <nav id="top" className="top-bar">
      <div className="top-bar-inner">
        <div className="sites links flex-items-baseline">
          <ul>
            <li>
              <a href="/servers">Dashboard</a>
            </li>
          </ul>
        </div>
        <div className="user-controls links flex flex-items-baseline flex-end">
          <div className="authenticated-controls">
            {LoginView}
          </div>
        </div>
      </div>
    </nav>
  </>
}