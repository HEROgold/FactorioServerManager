import { LoginForm } from "@/forms/Login"
import Layout from "../templates/Layout"
import Container from "@/components/Container"
import Panel from "@/templates/Panel"


export default function Login() {
  return <>
    <Layout>
      <title>Login</title>

      <Container>
        <Panel className="small-center">
          <h2>Log in</h2>
          <p>Use your Factorio.com account</p>
          <LoginForm />
        </Panel>
      </Container>
    </Layout>
  </>
}
