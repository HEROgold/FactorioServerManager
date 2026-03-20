import Separator from "./Separator";

export interface User {
  authenticated: boolean;
  display_name: string;
}

interface Props {
  user: User
}

/**
 * View for when user is already logged in
 */
function LoggedInView({user}: Props) {
  return <>
    <a href="{{url_for('dashboard.index')}}">{ user.display_name }</a>
    <Separator color={"#7dcaed"} />
    <a href="{{url_for('login.logout')}}">Log out</a>
  </>
}

/**
 * View for when a user still has to log in
 */
function HasToLogInView() {
  return <a href="{{url_for('login.login')}}">Log in</a>
}

export default function Navbar({user}: Props) {
  const LoginView = user.authenticated ? <LoggedInView user={user}/> : <HasToLogInView/>

  return <>
    <nav id="top" className="top-bar">
      <div className="top-bar-inner">
        <div className="sites links flex-items-baseline">
          <ul>
            <li><a href="{{ url_for('dashboard.index')}}">Dashboard</a></li>
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