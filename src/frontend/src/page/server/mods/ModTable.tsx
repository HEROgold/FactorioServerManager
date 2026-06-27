import ModRow, { type ModRowData } from "./ModRow";
import type { InstalledMod, ModRelease } from "./types";

interface RowSpec {
  mod: ModRowData;
  installed?: InstalledMod;
}

interface Props {
  mode: "download" | "installed";
  rows: RowSpec[];
  onInstall: (modName: string, version: string) => void | Promise<void>;
  onToggle: (mod: InstalledMod) => void;
  onRemove: (mod: InstalledMod) => void;
  loadReleases: (modName: string) => Promise<ModRelease[]>;
  installDisabled?: boolean;
}

// Shared table shell for both mod sub-tabs: a header plus one ModRow per mod.
export default function ModTable({
  mode,
  rows,
  onInstall,
  onToggle,
  onRemove,
  loadReleases,
  installDisabled,
}: Props) {
  return (
    <table className="mod-table">
      <thead>
        <tr>
          <th>Mod</th>
          <th>Version</th>
          <th className="mod-row-actions">{mode === "installed" ? "Manage" : "Download"}</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(({ mod, installed }) => (
          <ModRow
            key={mod.name}
            mod={mod}
            mode={mode}
            installed={installed}
            onInstall={onInstall}
            onToggle={onToggle}
            onRemove={onRemove}
            loadReleases={loadReleases}
            installDisabled={installDisabled}
          />
        ))}
      </tbody>
    </table>
  );
}
