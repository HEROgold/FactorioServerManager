import { LoginForm } from "@/forms/login"


export default function Login() {
  return <>
    <title>Login</title>

    <div className="container-inner">
      <div className="panel small-center">
        <h2>Log in</h2>
        <p>Use your Factorio.com account</p>
          <LoginForm />
      </div>
    </div>

  </>
}
