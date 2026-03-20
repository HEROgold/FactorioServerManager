import type { Version } from "@/types/GameVersion"
import { Form, useNavigation, useParams } from "react-router-dom"
import CSRF from "./CSRF"
import { SubmitButton } from "./SubmitButton"

interface InstallData {
  name: string
  version: Version
  port: number
}

export default function InstallForm({ version = "latest", port = 1234 }: InstallData) {
  const { name } = useParams()

  return <>
    <Form method="post" action={`/servers/${name}/install`}>
      <CSRF />
      <input type="text" name="name">{name}</input>
      <input type="text" name="version">{version}</input>
      <input type="text" name="port">{port}</input>
      <SubmitButton/>
    </Form>
  </>
}
