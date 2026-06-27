import { useCallback, useEffect, useState } from "react";
import { getJSON, sendJSON } from "@/api";
import Input from "@/components/tags/Input";
import Button from "@/components/tags/Button";
import InstalledList from "../mods/InstalledList";
import SearchResults from "../mods/SearchResults";
import Detail from "../mods/Detail";
import type {
  DetailResponse,
  InstalledMod,
  ModsIndexResponse,
  MutationResponse,
  SearchResponse,
} from "../mods/types";

// Mod-manager body, rendered as the Mods tab of the unified server-detail page.
export default function ModsTab({ name }: { name: string }) {
  const [index, setIndex] = useState<ModsIndexResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState<SearchResponse | null>(null);
  const [searching, setSearching] = useState(false);

  const [detail, setDetail] = useState<DetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const loadIndex = useCallback(async () => {
    try {
      setIndex(await getJSON<ModsIndexResponse>(`/api/server/${name}/mods`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load mods");
    }
  }, [name]);

  useEffect(() => { void loadIndex(); }, [loadIndex]);

  const runSearch = useCallback(async (q: string, p: number) => {
    if (!q) {
      setSearch(null);
      return;
    }
    setSearching(true);
    try {
      const params = new URLSearchParams({ q, page: String(p) });
      setSearch(await getJSON<SearchResponse>(`/api/server/${name}/mods/search?${params.toString()}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setSearching(false);
    }
  }, [name]);

  const handleSearchSubmit = (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmittedQuery(query);
    setPage(1);
    void runSearch(query, 1);
  };

  const handlePage = (p: number) => {
    setPage(p);
    void runSearch(submittedQuery, p);
  };

  const handleSelect = async (modName: string) => {
    setDetailLoading(true);
    try {
      setDetail(await getJSON<DetailResponse>(`/api/server/${name}/mods/detail/${modName}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load mod detail");
    } finally {
      setDetailLoading(false);
    }
  };

  const applyMutation = (res: MutationResponse) => {
    setIndex((prev) => (prev ? { ...prev, installed_mods: res.installed_mods } : prev));
  };

  const handleInstall = async (modName: string, version: string) => {
    try {
      const res = await sendJSON<MutationResponse>(`/api/server/${name}/mods/install`, "POST", { mod_name: modName, version });
      applyMutation(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Install failed");
    }
  };

  const handleToggle = async (mod: InstalledMod) => {
    try {
      const res = await sendJSON<MutationResponse>(`/api/server/${name}/mods/state`, "POST", {
        mod_name: mod.name,
        enabled: !mod.enabled,
      });
      applyMutation(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to toggle mod");
    }
  };

  const handleRemove = async (mod: InstalledMod) => {
    if (!confirm(`Remove ${mod.name}?`)) return;
    try {
      const res = await sendJSON<MutationResponse>(`/api/server/${name}/mods/${mod.name}`, "DELETE");
      applyMutation(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove mod");
    }
  };

  const installed = index?.installed_mods ?? [];

  return (
    <div>
      {error ? <p className="red">{error}</p> : null}

      <div className="panel-inset-lighter">
        <div className="flex" style={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
          <span>Factorio version: <strong>{index?.factorio_version || "Unknown"}</strong></span>
          <span>Total mods: <strong>{installed.length}</strong></span>
        </div>
        <hr />
        <div id="installed-mods">
          <InstalledList mods={installed} onToggle={handleToggle} onRemove={handleRemove} />
        </div>
      </div>

      <div className="panel-inset-lighter mt24">
        <h3 className="mt0">Browse the Mod Portal</h3>
        <form onSubmit={handleSearchSubmit} className="mod-search-bar" style={{ display: "flex", gap: "8px" }}>
          <Input
            type="search"
            name="q"
            placeholder="Search mods…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{ flex: 1 }}
          />
          <Button type="submit">Search</Button>
        </form>

        <div className="mod-portal-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "24px", marginTop: "16px" }}>
          <div id="mod-search-results">
            <SearchResults
              data={search}
              query={submittedQuery}
              loading={searching}
              onSelect={handleSelect}
              onPage={handlePage}
            />
          </div>
          <div id="mod-detail-content">
            <Detail data={detail} loading={detailLoading} onInstall={handleInstall} />
          </div>
        </div>
      </div>
    </div>
  );
}
