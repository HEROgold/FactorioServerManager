import { Form, useNavigation } from "react-router-dom"
import CSRF from "./CSRF"
import { SubmitButton } from "./SubmitButton"

type Build = ""
type Distro = ""
type Version = ""

interface DownloadData {
  build: Build
  distro: Distro
  version: Version
}

/**
 * Submit the form, and start download the server version.
 * @returns 
 */
export function DownloadForm(data: DownloadData) {
  const navigation = useNavigation();

  return <>
    <Form method="post" action="files/download_server">
      <CSRF />
      <input type="text" name="build">{data.build}</input>
      <input type="text" name="distro">{data.distro}</input>
      <input type="text" name="version">{data.version}</input>
      <SubmitButton isSubmitting={navigation.state === "submitting"} />
    </Form>
  </>
}
