import Placeholder from "@/components/tags/Placeholder";
import Card from "@/components/tags/Card";
import ButtonGhost from "@/components/tags/ButtonGhost";
import type { SearchResponse, SearchResult } from "./types";

interface Props {
  data: SearchResponse | null;
  query: string;
  loading: boolean;
  onSelect: (modName: string) => void;
  onPage: (page: number) => void;
}

export default function SearchResults({ data, query, loading, onSelect, onPage }: Props) {
  if (loading) {
    return <Placeholder><p>Searching…</p></Placeholder>;
  }
  if (data?.error) {
    return <Placeholder alert>{data.error}</Placeholder>;
  }
  if (!query) {
    return <Placeholder><p>Type at least one character to start exploring mods.</p></Placeholder>;
  }
  if (!data || data.results.length === 0) {
    return <Placeholder><p>No mods matched “{query}”. Try a different keyword.</p></Placeholder>;
  }

  const { results, pagination } = data;

  return (
    <>
      <div className="mod-search-grid">
        {results.map((mod: SearchResult) => (
          <Card
            key={mod.name}
            role="button"
            tabIndex={0}
            onClick={() => onSelect(mod.name)}
            onKeyDown={(e) => { if (e.key === "Enter") onSelect(mod.name); }}
          >
            {mod.thumbnail ? (
              <div className="mod-card-thumb" role="presentation" style={{ backgroundImage: `url('${mod.thumbnail}')` }} />
            ) : (
              <div className="mod-card-thumb mod-card-thumb-empty" role="presentation" />
            )}
            <div className="mod-card-body">
              <h4>{mod.title}</h4>
              <p>{mod.summary || "No summary provided yet."}</p>
              <div className="mod-card-meta">
                <span>{mod.owner || "Unknown creator"}</span>
                {mod.latest_release?.version ? <span>v{mod.latest_release.version}</span> : null}
                {mod.compatibility ? <span>Factorio {mod.compatibility}</span> : null}
                <span>{mod.downloads.toLocaleString()} downloads</span>
              </div>
            </div>
          </Card>
        ))}
      </div>
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
