import { useState } from "react"
import { useAvailableVersions } from "@/contexts/AvailableVersion"

const ARCHIVE_URL = "https://www.factorio.com/download/archive"

/**
 * Lets the user browse the available Factorio versions (fetched from
 * `/api/versions`) and jump to the official download archive.
 */
export function DownloadForm() {
  const { versions, loading, hasError } = useAvailableVersions()
  const [selected, setSelected] = useState<string>("")

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); window.open(ARCHIVE_URL, "_blank", "noreferrer") }}
      style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}
    >
      <select
        name="version"
        className="button"
        value={selected}
        onChange={(e) => setSelected(e.target.value)}
        disabled={loading || hasError}
      >
        {loading ? (
          <option value="">Loading versions…</option>
        ) : hasError ? (
          <option value="">Versions unavailable</option>
        ) : (
          versions.map((version) => (
            <option key={version} value={version}>{version}</option>
          ))
        )}
      </select>
      <button className="button" type="submit">Open Factorio Archive</button>
    </form>
  )
}
