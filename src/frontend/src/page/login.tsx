import { LoginForm } from "@/forms/Login"
import Layout from "../templates/Layout"


export default function Login() {
  return <>
  <Layout>
    <title>Login</title>

    <div className="container-inner">
      <div className="panel small-center">
        <h2>Log in</h2>
        <p>Use your Factorio.com account</p>
          <LoginForm />
      </div>
    </div>
  </Layout>
  </>
}
