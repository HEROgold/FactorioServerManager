import { useEffect, useState } from "react"
import type { Version } from "@/types/GameVersion"
import { useNavigate, useParams } from "react-router-dom"
import { SubmitButton } from "./SubmitButton"
import Input from "@/components/tags/Input"
import Select from "@/components/tags/Select"
import LoginRequired from "@/components/LoginRequired"
import { useAvailableVersions } from "@/contexts/AvailableVersion"
import { apiFetch } from "@/api"

interface InstallData {
  name?: string
  version?: Version
  port?: number
}

export default function InstallForm({ name, version = "stable", port = 34197 }: InstallData) {
  const fallbackName = name || useParams().name || "Factorio Server"
  const navigate = useNavigate()
  const { versions, loading, hasError } = useAvailableVersions()
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [unauthorized, setUnauthorized] = useState(false)
  const [selectedVersion, setSelectedVersion] = useState<string>("")

  // The select is controlled so the default survives the async versions load.
  // Preference order: an already-picked value, the requested `version`, then
  // "stable", then the first available version.
  useEffect(() => {
    if (!versions.length) return
    setSelectedVersion((prev) => {
      if (prev && versions.includes(prev as Version)) return prev
      if (versions.includes(version)) return version
      if (versions.includes("stable" as Version)) return "stable"
      return versions[0] ?? ""
    })
  }, [versions, version])

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    const form = e.currentTarget
    const value = (n: string) => (form.elements.namedItem(n) as HTMLInputElement | HTMLSelectElement | null)?.value
    const serverName = (value("name") || fallbackName).trim()
    const selected = selectedVersion || value("version") || "stable"
    const selectedPort = value("port")

    const params = new URLSearchParams({ version: selected })
    if (selectedPort) {
      params.set("port", selectedPort)
    }

    try {
      const res = await apiFetch(`/api/server/${encodeURIComponent(serverName)}/create?${params.toString()}`, {
        method: "POST",
      })
      if (res.status === 401) {
        setUnauthorized(true)
        setSubmitting(false)
        return
      }
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        throw new Error(data.detail || `Install failed: ${res.status}`)
      }
      // The backend sanitizes the name; navigate to the name it actually
      // created (falling back to the input) so we don't 404 on a renamed server.
      navigate(`/servers/${data.name || serverName}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Install failed")
      setSubmitting(false)
    }
  }

  if (unauthorized) {
    return <LoginRequired message="Please log in to create a server." />
  }

  return (
    <form onSubmit={handleSubmit} className="form-stack">
      <div className="field">
        <label htmlFor="install-name">Server Name</label>
        <Input type="text" id="install-name" name="name" placeholder={fallbackName} style={{ width: "100%" }} />
      </div>
      <div className="field">
        <label htmlFor="install-version">Factorio Version</label>
        <Select
          id="install-version"
          name="version"
          value={selectedVersion}
          onChange={(e) => setSelectedVersion(e.target.value)}
          disabled={loading || hasError}
          style={{ width: "100%" }}
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
        </Select>
      </div>
      <div className="field">
        <label htmlFor="install-port">Game Port</label>
        <Input type="number" id="install-port" name="port" min={1} max={65535} step={1} placeholder={`${port}`} style={{ width: "100%" }} />
      </div>
      {error ? <p className="red">{error}</p> : null}
      <SubmitButton busy="Installing..." idle="Install" submitting={submitting} />
    </form>
  )
}
