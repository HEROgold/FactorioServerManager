import { useNavigation } from "react-router-dom"
import CSRF from "./CSRF"
import { SubmitButton } from "./SubmitButton"
import type { Build, Distro, Version } from "@/types/GameVersion"
import Input from "@/components/tags/Input"


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
    <form method="post" action="files/download_server">
      <CSRF />
      <input type="text" name="build" value={data.build} />
      <input type="text" name="distro" value={data.distro} />
      <input type="text" name="version" value={data.version} />
      <SubmitButton busy="Downloading..." idle="Download" />
    </form>
  </>
}
