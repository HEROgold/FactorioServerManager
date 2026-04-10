import type { Version } from "@/types/GameVersion"
import { useParams } from "react-router-dom"
import CSRF from "./CSRF"
import { SubmitButton } from "./SubmitButton"
import Input from "@/components/tags/Input"
import { useAvailableVersions } from "@/contexts/AvailableVersion"

interface InstallData {
  name?: string
  version?: Version
  port?: number
}

export default function InstallForm({ name, version = "latest", port = 1234 }: InstallData) {
  const serverName = name || useParams().name || "Factorio Server"
  const { versions, loading, hasError } = useAvailableVersions()

  const defaultVersion = versions.includes(version)
    ? version
    : (versions.includes("latest") ? "latest" : (versions[0] ?? ""))

  return <>
    <form method="post" action={`/servers/${serverName}/install`}>
      <CSRF />
      <Input type="text" name="name" placeholder={serverName} />
      <select
        name="version"
        className="button"
        defaultValue={defaultVersion}
        disabled={loading || hasError}
      >
        {loading ? (
          <option value="">Loading versions...</option>
        ) : hasError ? (
          <option value="">Versions unavailable</option>
        ) : (
          versions.map((availableVersion) => (
            <option key={availableVersion} value={availableVersion}>
              {availableVersion}
            </option>
          ))
        )}
      </select>
      <Input type="number" name="port" placeholder={`${port}`} />
      <SubmitButton busy="Installing..." idle="Install" />
    </form>
  </>
}
