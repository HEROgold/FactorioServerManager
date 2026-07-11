import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { getJSON, sendJSON } from "@/api";
import { useFeatureFlags } from "@/contexts/FeatureFlags";
import type { FeatureFlags } from "@/types/featureFlags";
import Input from "@/components/tags/Input";
import Button from "@/components/tags/Button";
import Placeholder from "@/components/tags/Placeholder";
import ModTable from "../mods/ModTable";
import SearchResults from "../mods/SearchResults";
import type {
  InstalledMod,
  ModRelease,
  ModsIndexResponse,
  MutationResponse,
  SearchResponse,
} from "../mods/types";

const SUBTABS = ["installed", "download"] as const;
type SubTab = (typeof SUBTABS)[number];
const SUBTAB_LABELS: Record<SubTab, string> = {
  installed: "Installed",
  download: "Download",
};

// Each sub-tab is gated by a nested Mods flag (see the backend FeatureFlags.Mods).
const SUBTAB_ENABLED: Record<SubTab, (flags: FeatureFlags) => boolean> = {
  installed: (flags) => flags.Mods.manage,
  download: (flags) => flags.Mods.download,
};

// Mod-manager body, rendered as the Mods tab of the unified server-detail page.
// Split into two sub-tabs: "Installed" manages local mods, "Download" searches
// the Factorio mod portal. Each tab is a single table — one row per mod.
export default function ModsTab({ name }: { name: string }) {
  const [index, setIndex] = useState<ModsIndexResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { flags } = useFeatureFlags();
  const visibleSubTabs = useMemo(
    () => SUBTABS.filter((tab) => SUBTAB_ENABLED[tab](flags)),
    [flags],
  );

  const [subTab, setSubTab] = useState<SubTab>("installed");
  // The effective sub-tab: fall back to the first visible one if the selected
  // sub-tab is gated off (e.g. its flag is toggled off mid-session).
  const activeSubTab: SubTab | undefined = visibleSubTabs.includes(subTab)
    ? subTab
    : visibleSubTabs[0];

  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [search, setSearch] = useState<SearchResponse | null>(null);
  const [searching, setSearching] = useState(false);

  // Per-mod release lists, fetched lazily for the per-row version dropdowns.
  const releasesCache = useRef<Map<string, ModRelease[]>>(new Map());

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
    void runSearch(query, 1);
  };

  const handlePage = (p: number) => {
    void runSearch(submittedQuery, p);
  };

  const loadReleases = useCallback(async (modName: string): Promise<ModRelease[]> => {
    const cached = releasesCache.current.get(modName);
    if (cached) return cached;
    const res = await getJSON<{ releases: ModRelease[] }>(`/api/server/${name}/mods/detail/${modName}`);
    releasesCache.current.set(modName, res.releases);
    return res.releases;
  }, [name]);

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

  const installed = useMemo(() => index?.installed_mods ?? [], [index]);
  const installedByName = useMemo(
    () => new Map(installed.map((mod) => [mod.name, mod])),
    [installed],
  );
  const tokenMissing = index?.token_missing ?? false;

  return (
    <div>
      {error ? <p className="red">{error}</p> : null}

      <div className="panel-inset-lighter">
        <div className="flex" style={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
          <span>Factorio version: <strong>{index?.factorio_version || "Unknown"}</strong></span>
          <span>Total mods: <strong>{installed.length}</strong></span>
        </div>

        <nav className="server-tabs mod-subtabs">
          {visibleSubTabs.map((tab) => (
            <button
              key={tab}
              type="button"
              className={`server-tab${tab === activeSubTab ? " active" : ""}`}
              onClick={() => setSubTab(tab)}
            >
              {SUBTAB_LABELS[tab]}
            </button>
          ))}
        </nav>

        {activeSubTab === undefined ? (
          <Placeholder><p>Mod management is currently unavailable.</p></Placeholder>
        ) : activeSubTab === "download" ? (
          <>
            <form onSubmit={handleSearchSubmit} className="mod-search-bar" style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
              <Input
                type="search"
                name="q"
                placeholder="Search the mod portal…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                style={{ flex: 1 }}
              />
              <Button type="submit">Search</Button>
            </form>
            {submittedQuery ? (
              <SearchResults
                data={search}
                query={submittedQuery}
                loading={searching}
                installedByName={installedByName}
                installDisabled={tokenMissing}
                onInstall={handleInstall}
                onToggle={handleToggle}
                onRemove={handleRemove}
                loadReleases={loadReleases}
                onPage={handlePage}
              />
            ) : (
              <Placeholder><p>Search the Factorio mod portal above to add new mods.</p></Placeholder>
            )}
          </>
        ) : installed.length === 0 ? (
          <Placeholder><p>No mods installed yet. Use the Download tab to add some.</p></Placeholder>
        ) : (
          <ModTable
            mode="installed"
            rows={installed.map((mod) => ({
              mod: { name: mod.name, title: mod.name, latestVersion: mod.version },
              installed: mod,
            }))}
            installDisabled={tokenMissing}
            onInstall={handleInstall}
            onToggle={handleToggle}
            onRemove={handleRemove}
            loadReleases={loadReleases}
          />
        )}
      </div>
    </div>
  );
}
