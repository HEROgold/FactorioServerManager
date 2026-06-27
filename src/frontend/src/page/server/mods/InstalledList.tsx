import Checkbox from "@/components/tags/Checkbox";
import Button from "@/components/tags/Button";
import type { InstalledMod } from "./types";

interface Props {
  mods: InstalledMod[];
  onToggle: (mod: InstalledMod) => void;
  onRemove: (mod: InstalledMod) => void;
}

export default function InstalledList({ mods, onToggle, onRemove }: Props) {
  if (!mods.length) {
    return <p className="mb0">No mods installed for this server.</p>;
  }

  return (
    <table className="table installed-mods-table">
      <thead>
        <tr>
          <th scope="col">Mod</th>
          <th scope="col">Version</th>
          <th scope="col">Enabled</th>
          <th scope="col">Actions</th>
        </tr>
      </thead>
      <tbody>
        {mods.map((mod) => (
          <tr key={mod.name}>
            <td><strong>{mod.name}</strong></td>
            <td>{mod.version || "—"}</td>
            <td>
              <Checkbox
                checked={mod.enabled}
                disabled={mod.is_core}
                onChange={() => onToggle(mod)}
                aria-label={`Toggle ${mod.name}`}
              />
            </td>
            <td>
              {mod.is_core ? (
                <span className="muted">core</span>
              ) : (
                <Button variant="red" type="button" onClick={() => onRemove(mod)}>
                  Remove
                </Button>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
