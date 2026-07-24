import { useEffect, useRef, useState } from "react"
import type { Version } from "@/types/GameVersion"
import { useNavigate, useParams } from "react-router-dom"
import { SubmitButton } from "./SubmitButton"
import Input from "@/components/tags/Input"
import Select from "@/components/tags/Select"
import LoginRequired from "@/components/LoginRequired"
import { useAvailableVersions } from "@/contexts/AvailableVersion"
import { ApiError, getJSON, sendJSON } from "@/api"

interface InstallData {
  name?: string
  version?: Version
  port?: number
}

interface PortLimits {
  lower: number
  upper: number
  default: number
}

export default function InstallForm({ name, version = "stable", port = 34197 }: InstallData) {
  const fallbackName = name || useParams().name || "Factorio Server"
  const navigate = useNavigate()
  const { versions, loading, hasError } = useAvailableVersions()
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [unauthorized, setUnauthorized] = useState(false)
  const [selectedVersion, setSelectedVersion] = useState<string>("")

  // Port bounds are operator-configurable on the backend; until they load we
  // fall back to the full valid TCP/UDP range so the field is never unbounded.
  const [limits, setLimits] = useState<PortLimits>({ lower: 1, upper: 65535, default: port })
  const [portValue, setPortValue] = useState<string>(String(port))
  // Don't overwrite a value the user has already typed when the limits arrive.
  const portTouched = useRef(false)

  useEffect(() => {
    let cancelled = false
    getJSON<PortLimits>("/api/port-limits")
      .then((fetched) => {
        if (cancelled) return
        setLimits(fetched)
        if (!portTouched.current) setPortValue(String(fetched.default))
      })
      .catch(() => {
        // Keep the fallback range on failure; the backend still validates.
      })
    return () => {
      cancelled = true
    }
  }, [])

  // Coerce an entry into the configured range. HTML min/max only constrain the
  // spinner and validity — they do NOT clamp typed values — so we do it here.
  const clampPort = (raw: string): string => {
    const parsed = Number.parseInt(raw, 10)
    if (Number.isNaN(parsed)) return String(limits.default)
    return String(Math.min(Math.max(parsed, limits.lower), limits.upper))
  }

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
    // Always submit a clamped, in-range port so the backend never 422s on a
    // value the user could type past the spinner bounds.
    const selectedPort = clampPort(portValue)
    setPortValue(selectedPort)

    const params = new URLSearchParams({ version: selected })
    if (selectedPort) {
      params.set("port", selectedPort)
    }

    try {
      // Route through sendJSON so the double-submit CSRF token is attached;
      // a bare apiFetch POST omits it and the backend rejects the request.
      const data = await sendJSON<{ name?: string }>(
        `/api/server/${encodeURIComponent(serverName)}/create?${params.toString()}`,
        "POST",
      )
      // The backend sanitizes the name; navigate to the name it actually
      // created (falling back to the input) so we don't 404 on a renamed server.
      navigate(`/servers/${data.name || serverName}`)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setUnauthorized(true)
        setSubmitting(false)
        return
      }
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
        <Input
          type="number"
          id="install-port"
          name="port"
          min={limits.lower}
          max={limits.upper}
          step={1}
          value={portValue}
          onChange={(e) => {
            portTouched.current = true
            setPortValue(e.target.value)
          }}
          onBlur={(e) => setPortValue(clampPort(e.target.value))}
          placeholder={`${limits.default}`}
          style={{ width: "100%" }}
        />
        <small style={{ opacity: 0.8 }}>Allowed range: {limits.lower}–{limits.upper}</small>
      </div>
      {error ? <p className="red">{error}</p> : null}
      <SubmitButton busy="Installing..." idle="Install" submitting={submitting} />
    </form>
  )
}
