import type { Version } from "@/types/GameVersion"
import { useParams } from "react-router-dom"
import CSRF from "./CSRF"
import { SubmitButton } from "./SubmitButton"
import Input from "@/components/tags/Input"

interface InstallData {
  name: string
  version: Version
  port: number
}

export default function InstallForm({ version = "latest", port = 1234 }: InstallData) {
  const { name } = useParams()

  return <>
    <form method="post" action={`/servers/${name}/install`}>
      <CSRF />
      <Input type="text" name="name" placeholder={name} />
      <Input type="text" name="version" placeholder={version} />
      <Input type="number" name="port" placeholder={`${port}`} />
      <SubmitButton busy="Installing..." idle="Install" />
    </form>
  </>
}
