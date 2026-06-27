/** Shared types for the mod manager, mirroring the API JSON payloads. */

export interface InstalledMod {
  name: string;
  enabled: boolean;
  version: string | null;
  has_archive: boolean;
  is_core: boolean;
  /** Loadable by the game: has a downloadable archive or ships bundled with it. */
  playable: boolean;
}

/** Releases fetched lazily per mod for the per-card version dropdown. */
export type ReleasesByMod = Record<string, ModRelease[]>;

export interface ModsIndexResponse {
  installed_mods: InstalledMod[];
  factorio_version: string | null;
  factorio_version_line: string | null;
  token_missing: boolean;
}

export interface SearchResult {
  name: string;
  title: string;
  summary: string | null;
  owner: string | null;
  downloads: number;
  score: number;
  thumbnail: string | null;
  latest_release: { version?: string } & Record<string, unknown>;
  compatibility: string | null;
}

export interface Pagination {
  page: number;
  has_prev: boolean;
  has_next: boolean;
}

export interface SearchResponse {
  results: SearchResult[];
  query: string;
  pagination: Pagination;
  error: string | null;
}

export interface ModRelease {
  version: string;
  factorio_version: string | null;
  released_at: string;
  download_url: string | null;
  file_name: string | null;
  size_label: string | null;
  dependencies: string[];
  is_recommended: boolean;
}

export interface DetailResponse {
  mod: {
    name?: string;
    title?: string;
    summary?: string;
    category?: string;
    thumbnail?: string | null;
    tags?: string[];
  };
  releases: ModRelease[];
  token_missing: boolean;
  error: string | null;
}

export interface MutationResponse {
  installed_mods: InstalledMod[];
  action: string;
  name: string;
}
