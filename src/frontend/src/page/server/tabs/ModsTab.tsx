import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
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

// The effective sub-tab: fall back to the first visible one if the selected
// sub-tab is gated off (e.g. its flag is toggled off mid-session).
function useActiveSubTab(flags: FeatureFlags) {
  const visibleSubTabs = useMemo(
    () => SUBTABS.filter((tab) => SUBTAB_ENABLED[tab](flags)),
    [flags],
  );
  const [subTab, setSubTab] = useState<SubTab>("installed");
  const activeSubTab: SubTab | undefined = visibleSubTabs.includes(subTab)
    ? subTab
    : visibleSubTabs[0];

  return { visibleSubTabs, activeSubTab, setSubTab };
}

function useModsIndex(name: string, setError: (message: string | null) => void) {
  const [index, setIndex] = useState<ModsIndexResponse | null>(null);

  const loadIndex = useCallback(async () => {
    try {
      setIndex(await getJSON<ModsIndexResponse>(`/api/server/${name}/mods`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load mods");
    }
  }, [name, setError]);

  useEffect(() => { void loadIndex(); }, [loadIndex]);

  return [index, setIndex] as const;
}

function useModSearch(name: string, setError: (message: string | null) => void) {
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [search, setSearch] = useState<SearchResponse | null>(null);
  const [searching, setSearching] = useState(false);

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
  }, [name, setError]);

  const handleSearchSubmit = (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmittedQuery(query);
    void runSearch(query, 1);
  };

  const handlePage = (p: number) => {
    void runSearch(submittedQuery, p);
  };

  return { query, setQuery, submittedQuery, search, searching, handleSearchSubmit, handlePage };
}

function useReleasesLoader(name: string) {
  // Per-mod release lists, fetched lazily for the per-row version dropdowns.
  const releasesCache = useRef<Map<string, ModRelease[]>>(new Map());

  return useCallback(async (modName: string): Promise<ModRelease[]> => {
    const cached = releasesCache.current.get(modName);
    if (cached) return cached;
    const res = await getJSON<{ releases: ModRelease[] }>(`/api/server/${name}/mods/detail/${modName}`);
    releasesCache.current.set(modName, res.releases);
    return res.releases;
  }, [name]);
}

function useModMutations(
  name: string,
  setIndex: Dispatch<SetStateAction<ModsIndexResponse | null>>,
  setError: (message: string | null) => void,
) {
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

  return { handleInstall, handleToggle, handleRemove };
}

interface DownloadSubTabProps {
  query: string;
  setQuery: (value: string) => void;
  submittedQuery: string;
  search: SearchResponse | null;
  searching: boolean;
  installedByName: Map<string, InstalledMod>;
  tokenMissing: boolean;
  onSearchSubmit: (e: React.SubmitEvent<HTMLFormElement>) => void;
  onPage: (page: number) => void;
  onInstall: (modName: string, version: string) => void | Promise<void>;
  onToggle: (mod: InstalledMod) => void;
  onRemove: (mod: InstalledMod) => void;
  loadReleases: (modName: string) => Promise<ModRelease[]>;
}

function ModSearchBar({
  query,
  setQuery,
  onSubmit,
}: {
  query: string;
  setQuery: (value: string) => void;
  onSubmit: (e: React.SubmitEvent<HTMLFormElement>) => void;
}) {
  return (
    <form onSubmit={onSubmit} className="mod-search-bar" style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
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
  );
}

function DownloadSubTab({
  query,
  setQuery,
  submittedQuery,
  search,
  searching,
  installedByName,
  tokenMissing,
  onSearchSubmit,
  onPage,
  onInstall,
  onToggle,
  onRemove,
  loadReleases,
}: DownloadSubTabProps) {
  return (
    <>
      <ModSearchBar query={query} setQuery={setQuery} onSubmit={onSearchSubmit} />
      {submittedQuery ? (
        <SearchResults
          data={search}
          query={submittedQuery}
          loading={searching}
          installedByName={installedByName}
          installDisabled={tokenMissing}
          onInstall={onInstall}
          onToggle={onToggle}
          onRemove={onRemove}
          loadReleases={loadReleases}
          onPage={onPage}
        />
      ) : (
        <Placeholder><p>Search the Factorio mod portal above to add new mods.</p></Placeholder>
      )}
    </>
  );
}

function InstalledSubTab({
  installed,
  tokenMissing,
  onInstall,
  onToggle,
  onRemove,
  loadReleases,
}: {
  installed: InstalledMod[];
  tokenMissing: boolean;
  onInstall: (modName: string, version: string) => void | Promise<void>;
  onToggle: (mod: InstalledMod) => void;
  onRemove: (mod: InstalledMod) => void;
  loadReleases: (modName: string) => Promise<ModRelease[]>;
}) {
  if (installed.length === 0) {
    return <Placeholder><p>No mods installed yet. Use the Download tab to add some.</p></Placeholder>;
  }
  return (
    <ModTable
      mode="installed"
      rows={installed.map((mod) => ({
        mod: { name: mod.name, title: mod.name, latestVersion: mod.version },
        installed: mod,
      }))}
      installDisabled={tokenMissing}
      onInstall={onInstall}
      onToggle={onToggle}
      onRemove={onRemove}
      loadReleases={loadReleases}
    />
  );
}

function ModsTabHeader({
  factorioVersion,
  totalMods,
  visibleSubTabs,
  activeSubTab,
  onSelectSubTab,
}: {
  factorioVersion: string;
  totalMods: number;
  visibleSubTabs: readonly SubTab[];
  activeSubTab: SubTab | undefined;
  onSelectSubTab: (tab: SubTab) => void;
}) {
  return (
    <>
      <div className="flex" style={{ justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        <span>Factorio version: <strong>{factorioVersion}</strong></span>
        <span>Total mods: <strong>{totalMods}</strong></span>
      </div>

      <nav className="server-tabs mod-subtabs">
        {visibleSubTabs.map((tab) => (
          <button
            key={tab}
            type="button"
            className={`server-tab${tab === activeSubTab ? " active" : ""}`}
            onClick={() => onSelectSubTab(tab)}
          >
            {SUBTAB_LABELS[tab]}
          </button>
        ))}
      </nav>
    </>
  );
}

interface ActiveModsSubTabProps {
  activeSubTab: SubTab | undefined;
  searchState: ReturnType<typeof useModSearch>;
  mutations: ReturnType<typeof useModMutations>;
  installed: InstalledMod[];
  installedByName: Map<string, InstalledMod>;
  tokenMissing: boolean;
  loadReleases: (modName: string) => Promise<ModRelease[]>;
}

function ActiveModsSubTab({
  activeSubTab,
  searchState,
  mutations,
  installed,
  installedByName,
  tokenMissing,
  loadReleases,
}: ActiveModsSubTabProps) {
  if (activeSubTab === undefined) {
    return <Placeholder><p>Mod management is currently unavailable.</p></Placeholder>;
  }
  if (activeSubTab === "download") {
    return (
      <DownloadSubTab
        query={searchState.query}
        setQuery={searchState.setQuery}
        submittedQuery={searchState.submittedQuery}
        search={searchState.search}
        searching={searchState.searching}
        installedByName={installedByName}
        tokenMissing={tokenMissing}
        onSearchSubmit={searchState.handleSearchSubmit}
        onPage={searchState.handlePage}
        onInstall={mutations.handleInstall}
        onToggle={mutations.handleToggle}
        onRemove={mutations.handleRemove}
        loadReleases={loadReleases}
      />
    );
  }
  return (
    <InstalledSubTab
      installed={installed}
      tokenMissing={tokenMissing}
      onInstall={mutations.handleInstall}
      onToggle={mutations.handleToggle}
      onRemove={mutations.handleRemove}
      loadReleases={loadReleases}
    />
  );
}

// Mod-manager body, rendered as the Mods tab of the unified server-detail page.
// Split into two sub-tabs: "Installed" manages local mods, "Download" searches
// the Factorio mod portal. Each tab is a single table — one row per mod.
export default function ModsTab({ name }: { name: string }) {
  const [error, setError] = useState<string | null>(null);
  const { flags } = useFeatureFlags();
  const { visibleSubTabs, activeSubTab, setSubTab } = useActiveSubTab(flags);

  const [index, setIndex] = useModsIndex(name, setError);
  const searchState = useModSearch(name, setError);
  const mutations = useModMutations(name, setIndex, setError);
  const loadReleases = useReleasesLoader(name);

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
        <ModsTabHeader
          factorioVersion={index?.factorio_version || "Unknown"}
          totalMods={installed.length}
          visibleSubTabs={visibleSubTabs}
          activeSubTab={activeSubTab}
          onSelectSubTab={setSubTab}
        />
        <ActiveModsSubTab
          activeSubTab={activeSubTab}
          searchState={searchState}
          mutations={mutations}
          installed={installed}
          installedByName={installedByName}
          tokenMissing={tokenMissing}
          loadReleases={loadReleases}
        />
      </div>
    </div>
  );
}
