import { Link, useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import Layout from "../../../templates/Layout";
import { useAuth } from "../../../hooks/useAuth";
import { useServerMods } from "../../../hooks/useAPI";
import { apiClient, APIError } from "../../../api/client";

interface Mod {
  name: string;
  enabled: boolean;
  version?: string;
}

interface ModSearchResult {
  name: string;
  title: string;
  summary: string;
  downloads_count: number;
  latest_release?: {
    version: string;
    released_at: string;
  };
}

function InstalledModItem({ mod, onToggle, onUninstall }: {
  mod: Mod;
  onToggle: (name: string, enabled: boolean) => void;
  onUninstall: (name: string) => void;
}) {
  const [isUpdating, setIsUpdating] = useState(false);

  const handleToggle = async () => {
    setIsUpdating(true);
    try {
      await onToggle(mod.name, !mod.enabled);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="panel-inset-lighter mb12 p12">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ flex: 1 }}>
          <strong>{mod.name}</strong>
          {mod.version && <span style={{ color: '#666', marginLeft: '8px' }}>v{mod.version}</span>}
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <input
              type="checkbox"
              checked={mod.enabled}
              onChange={handleToggle}
              disabled={isUpdating || mod.name === 'base'}
            />
            Enabled
          </label>
          {mod.name !== 'base' && (
            <button
              onClick={() => onUninstall(mod.name)}
              className="button button-red"
              style={{ fontSize: '0.875rem', padding: '4px 8px' }}
            >
              Uninstall
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function ModSearchItem({ mod, onAdd }: {
  mod: ModSearchResult;
  onAdd: (name: string, version?: string) => void;
}) {
  return (
    <div className="panel-inset-lighter mb12 p12">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <div style={{ flex: 1 }}>
          <strong>{mod.title}</strong>
          <div style={{ fontSize: '0.875rem', color: '#666' }}>{mod.name}</div>
          <p style={{ fontSize: '0.9rem', margin: '8px 0' }}>{mod.summary}</p>
          <div style={{ fontSize: '0.875rem', color: '#888' }}>
            Downloads: {mod.downloads_count.toLocaleString()}
            {mod.latest_release && ` | Latest: v${mod.latest_release.version}`}
          </div>
        </div>
        <button
          onClick={() => onAdd(mod.name, mod.latest_release?.version)}
          className="button"
          style={{ whiteSpace: 'nowrap' }}
        >
          Add to Install Queue
        </button>
      </div>
    </div>
  );
}

export default function ModManager() {
  const { name } = useParams();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  const { mods, loading, error, refetch } = useServerMods(name || '');

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<ModSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Batch installation queue
  const [installQueue, setInstallQueue] = useState<Array<{ mod_name: string; version?: string }>>([]);
  const [isInstalling, setIsInstalling] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, authLoading, navigate]);

  if (!name) {
    navigate("/servers");
    return null;
  }

  const handleSearch = async () => {
    setIsSearching(true);
    setSearchError(null);
    try {
      const results = await apiClient.searchMods(searchQuery, 1, 20, name);
      setSearchResults(results.results || []);
    } catch (err) {
      setSearchError(err instanceof APIError ? err.message : 'Search failed');
    } finally {
      setIsSearching(false);
    }
  };

  const addToQueue = (modName: string, version?: string) => {
    if (!installQueue.some(m => m.mod_name === modName)) {
      setInstallQueue([...installQueue, { mod_name: modName, version }]);
    }
  };

  const removeFromQueue = (modName: string) => {
    setInstallQueue(installQueue.filter(m => m.mod_name !== modName));
  };

  const handleBatchInstall = async () => {
    if (installQueue.length === 0) return;

    setIsInstalling(true);
    try {
      await apiClient.batchInstallMods(name, installQueue);
      setInstallQueue([]);
      // Refresh mod list after a delay to allow installation to complete
      setTimeout(() => refetch(), 2000);
      alert(`Installing ${installQueue.length} mods. This may take a few minutes.`);
    } catch (err) {
      alert('Batch installation failed: ' + (err instanceof APIError ? err.message : 'Unknown error'));
    } finally {
      setIsInstalling(false);
    }
  };

  const handleToggleMod = async (modName: string, enabled: boolean) => {
    try {
      await apiClient.toggleMod(name, modName, enabled);
      refetch();
    } catch (err) {
      alert('Failed to toggle mod: ' + (err instanceof APIError ? err.message : 'Unknown error'));
    }
  };

  const handleUninstall = async (modName: string) => {
    if (!confirm(`Are you sure you want to uninstall ${modName}?`)) return;

    try {
      await apiClient.uninstallMod(name, modName);
      refetch();
    } catch (err) {
      alert('Failed to uninstall mod: ' + (err instanceof APIError ? err.message : 'Unknown error'));
    }
  };

  if (authLoading || loading) {
    return (
      <Layout>
        <div className="container-inner">
          <div className="medium-center">
            <div className="panel mb64 pb0 m0 flex grow flex-column">
              <h2>Mod Manager</h2>
              <p>Loading...</p>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <title>{name} • Mods</title>
      <div className="container-inner">
        <div className="medium-center">
          <div className="panel mb64 flex flex-column">
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap', marginBottom: '24px' }}>
              <div style={{ flex: 1 }}>
                <h2 style={{ margin: 0 }}>{name} Mod Manager</h2>
                <p style={{ margin: '4px 0', color: '#666' }}>
                  Manage mods for your server
                </p>
              </div>
              <Link className="button button-ghost" to={`/servers/${name}/`}>
                Back to Server
              </Link>
            </div>

            {/* Installed Mods Section */}
            <div className="panel-inset-lighter mb12 p12">
              <h3>Installed Mods ({mods.length})</h3>
              {error && <p style={{ color: 'red' }}>{error}</p>}
              {mods.length === 0 ? (
                <p>No mods installed yet.</p>
              ) : (
                mods.map((mod) => (
                  <InstalledModItem
                    key={mod.name}
                    mod={mod}
                    onToggle={handleToggleMod}
                    onUninstall={handleUninstall}
                  />
                ))
              )}
            </div>

            {/* Mod Search Section */}
            <div className="panel-inset-lighter mb12 p12">
              <h3>Search & Install Mods</h3>
              <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                <input
                  type="text"
                  placeholder="Search mods..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  style={{ flex: 1 }}
                />
                <button onClick={handleSearch} disabled={isSearching} className="button">
                  {isSearching ? 'Searching...' : 'Search'}
                </button>
              </div>

              {searchError && <p style={{ color: 'red' }}>{searchError}</p>}

              {searchResults.length > 0 && (
                <div>
                  {searchResults.map((mod) => (
                    <ModSearchItem key={mod.name} mod={mod} onAdd={addToQueue} />
                  ))}
                </div>
              )}
            </div>

            {/* Install Queue Section */}
            {installQueue.length > 0 && (
              <div className="panel-inset-lighter mb12 p12" style={{ backgroundColor: '#f0f8ff' }}>
                <h3>Install Queue ({installQueue.length})</h3>
                {installQueue.map((mod) => (
                  <div key={mod.mod_name} style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>
                      {mod.mod_name}
                      {mod.version && <span style={{ color: '#666', marginLeft: '8px' }}>v{mod.version}</span>}
                    </span>
                    <button
                      onClick={() => removeFromQueue(mod.mod_name)}
                      className="button"
                      style={{ fontSize: '0.875rem', padding: '4px 8px' }}
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button
                  onClick={handleBatchInstall}
                  disabled={isInstalling}
                  className="button"
                  style={{ width: '100%', marginTop: '12px' }}
                >
                  {isInstalling ? 'Installing...' : `Install All (${installQueue.length} mods)`}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
