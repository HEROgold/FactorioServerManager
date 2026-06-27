import Placeholder from "@/components/tags/Placeholder";
import ButtonGhost from "@/components/tags/ButtonGhost";
import ModTable from "./ModTable";
import type { InstalledMod, ModRelease, SearchResponse, SearchResult } from "./types";

interface Props {
  data: SearchResponse | null;
  query: string;
  loading: boolean;
  installedByName: Map<string, InstalledMod>;
  installDisabled: boolean;
  onInstall: (modName: string, version: string) => void | Promise<void>;
  onToggle: (mod: InstalledMod) => void;
  onRemove: (mod: InstalledMod) => void;
  loadReleases: (modName: string) => Promise<ModRelease[]>;
  onPage: (page: number) => void;
}

export default function SearchResults({
  data,
  query,
  loading,
  installedByName,
  installDisabled,
  onInstall,
  onToggle,
  onRemove,
  loadReleases,
  onPage,
}: Props) {
  if (loading) {
    return <Placeholder><p>Searching…</p></Placeholder>;
  }
  if (data?.error) {
    return <Placeholder alert>{data.error}</Placeholder>;
  }
  if (!data || data.results.length === 0) {
    return <Placeholder><p>No mods matched “{query}”. Try a different keyword.</p></Placeholder>;
  }

  const { results, pagination } = data;

  return (
    <>
      <ModTable
        mode="download"
        rows={results.map((mod: SearchResult) => ({
          mod: {
            name: mod.name,
            title: mod.title,
            summary: mod.summary,
            owner: mod.owner,
            downloads: mod.downloads,
            thumbnail: mod.thumbnail,
            latestVersion: mod.latest_release?.version ?? null,
            compatibility: mod.compatibility,
          },
          installed: installedByName.get(mod.name),
        }))}
        installDisabled={installDisabled}
        onInstall={onInstall}
        onToggle={onToggle}
        onRemove={onRemove}
        loadReleases={loadReleases}
      />
      {(pagination.has_prev || pagination.has_next) && (
        <div className="mod-pagination">
          {pagination.has_prev && (
            <ButtonGhost className="button" type="button" onClick={() => onPage(pagination.page - 1)}>
              Previous
            </ButtonGhost>
          )}
          <span>Page {pagination.page}</span>
          {pagination.has_next && (
            <ButtonGhost className="button" type="button" onClick={() => onPage(pagination.page + 1)}>
              Next
            </ButtonGhost>
          )}
        </div>
      )}
    </>
  );
}
