import { useState } from "react";
import Button from "@/components/tags/Button";
import Select from "@/components/tags/Select";
import Checkbox from "@/components/tags/Checkbox";
import type { InstalledMod, ModRelease } from "./types";

export interface ModRowData {
  name: string;
  title: string;
  summary?: string | null;
  owner?: string | null;
  downloads?: number | null;
  thumbnail?: string | null;
  /** Latest known version, used as the default download target. */
  latestVersion?: string | null;
  compatibility?: string | null;
}

interface Props {
  mod: ModRowData;
  /** "download" lists portal results; "installed" manages local mods. */
  mode: "download" | "installed";
  /** Present when this mod is installed on the server. */
  installed?: InstalledMod;
  onInstall: (modName: string, version: string) => void | Promise<void>;
  onToggle: (mod: InstalledMod) => void;
  onRemove: (mod: InstalledMod) => void;
  /** Lazily load every release for the version dropdown. */
  loadReleases: (modName: string) => Promise<ModRelease[]>;
  /** Disable install controls (e.g. no Factorio token). */
  installDisabled?: boolean;
}

// One mod as a single table row. The version dropdown lazily loads the full
// release list on first focus; the action cell installs/enables/removes the
// version currently selected in that dropdown.
export default function ModRow({
  mod,
  mode,
  installed,
  onInstall,
  onToggle,
  onRemove,
  loadReleases,
  installDisabled,
}: Props) {
  const [releases, setReleases] = useState<ModRelease[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState("");

  const defaultVersion = installed?.version || mod.latestVersion || "";
  const chosenVersion = selected || defaultVersion;

  // Pull the full release list the first time the dropdown is touched.
  const ensureReleases = async () => {
    if (releases !== null || loading) return;
    setLoading(true);
    try {
      const loaded = await loadReleases(mod.name);
      setReleases(loaded);
      if (!selected) setSelected(loaded[0]?.version ?? defaultVersion);
    } finally {
      setLoading(false);
    }
  };

  const versionCell = (
    <Select
      value={chosenVersion}
      onFocus={() => void ensureReleases()}
      onChange={(e) => setSelected(e.target.value)}
      aria-label={`Version for ${mod.title}`}
      disabled={loading}
    >
      {releases && releases.length > 0 ? (
        releases.map((release) => (
          <option key={release.version} value={release.version}>
            v{release.version} • Factorio {release.factorio_version || "any"}
          </option>
        ))
      ) : (
        <option value={chosenVersion}>{chosenVersion ? `v${chosenVersion}` : "—"}</option>
      )}
    </Select>
  );

  return (
    <tr className="mod-row">
      <td className="mod-row-mod">
        {mod.thumbnail ? (
          <span className="mod-row-thumb" style={{ backgroundImage: `url('${mod.thumbnail}')` }} />
        ) : (
          <span className="mod-row-thumb mod-row-thumb-empty" />
        )}
        <span className="mod-row-text">
          <span className="mod-row-title">{mod.title}</span>
          <span className="mod-row-meta">
            {mod.owner ? <span>{mod.owner}</span> : null}
            {mod.compatibility ? <span>Factorio {mod.compatibility}</span> : null}
            {typeof mod.downloads === "number" ? <span>{mod.downloads.toLocaleString()} downloads</span> : null}
          </span>
          {mod.summary ? <span className="mod-row-summary">{mod.summary}</span> : null}
        </span>
      </td>
      <td className="mod-row-version">{versionCell}</td>
      <td className="mod-row-actions">
        {mode === "installed" && installed ? (
          <InstalledActions
            installed={installed}
            chosenVersion={chosenVersion}
            installDisabled={installDisabled}
            onToggle={onToggle}
            onRemove={onRemove}
            onInstall={onInstall}
          />
        ) : (
          <DownloadAction
            modName={mod.name}
            chosenVersion={chosenVersion}
            installed={installed}
            installDisabled={installDisabled}
            onInstall={onInstall}
          />
        )}
      </td>
    </tr>
  );
}

function DownloadAction({
  modName,
  chosenVersion,
  installed,
  installDisabled,
  onInstall,
}: {
  modName: string;
  chosenVersion: string;
  installed?: InstalledMod;
  installDisabled?: boolean;
  onInstall: (modName: string, version: string) => void | Promise<void>;
}) {
  const alreadyHasVersion = installed?.version && installed.version === chosenVersion;
  if (alreadyHasVersion) {
    return <Button variant="green" small type="button" disabled>Installed</Button>;
  }
  const label = installed ? `Update to v${chosenVersion}` : `Download v${chosenVersion}`;
  return (
    <Button
      variant="green"
      small
      type="button"
      disabled={installDisabled || !chosenVersion}
      onClick={() => chosenVersion && void onInstall(modName, chosenVersion)}
    >
      {chosenVersion ? label : "Download"}
    </Button>
  );
}

function InstalledActions({
  installed,
  chosenVersion,
  installDisabled,
  onToggle,
  onRemove,
  onInstall,
}: {
  installed: InstalledMod;
  chosenVersion: string;
  installDisabled?: boolean;
  onToggle: (mod: InstalledMod) => void;
  onRemove: (mod: InstalledMod) => void;
  onInstall: (modName: string, version: string) => void | Promise<void>;
}) {
  const versionChanged = !!chosenVersion && chosenVersion !== installed.version;
  return (
    <>
      <Checkbox
        checked={installed.enabled}
        disabled={installed.name === "base"}
        onChange={() => onToggle(installed)}
        label={installed.enabled ? "Enabled" : "Disabled"}
      />
      {versionChanged && !installed.is_core ? (
        <Button
          variant="green"
          small
          type="button"
          disabled={installDisabled}
          onClick={() => void onInstall(installed.name, chosenVersion)}
        >
          Install v{chosenVersion}
        </Button>
      ) : null}
      {installed.is_core ? (
        <span className="muted">core</span>
      ) : (
        <Button variant="red" small type="button" onClick={() => onRemove(installed)}>
          Remove
        </Button>
      )}
    </>
  );
}
