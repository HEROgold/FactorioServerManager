import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import Layout from "@/templates/Layout";
import StatusLight from "@/components/tags/StatusLight";
import { useServerStatus } from "@/hooks/useServerStatus";
import { getJSON } from "@/api";
import type { ManageServerData } from "@/forms/Settings";
import ManageTab from "./tabs/ManageTab";
import SettingsTab from "./tabs/SettingsTab";
import LogsTab from "./tabs/LogsTab";
import RconTab from "./tabs/RconTab";
import ModsTab from "./tabs/ModsTab";

interface ServerDetailData {
  name: string;
  ip: string;
  port: number;
  status: string;
  factorio_version: string | null;
}

const TABS = ["manage", "settings", "logs", "rcon", "mods"] as const;
type Tab = (typeof TABS)[number];

const TAB_LABELS: Record<Tab, string> = {
  manage: "Manage",
  settings: "Settings",
  logs: "Logs",
  rcon: "RCON",
  mods: "Mods",
};

function isTab(value: string | null): value is Tab {
  return value !== null && (TABS as readonly string[]).includes(value);
}

export default function ServerDetail() {
  const { name } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [detail, setDetail] = useState<ServerDetailData | null>(null);
  const [settings, setSettings] = useState<ManageServerData | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Log buffer lives here (not in LogsTab) so a manual "Clear" survives tab
  // switches — LogsTab unmounts when you leave the Logs tab.
  const [logLines, setLogLines] = useState<string[]>([]);
  const [logsCleared, setLogsCleared] = useState(false);
  const logsSeededRef = useRef(false);

  const activeTab: Tab = isTab(searchParams.get("tab")) ? (searchParams.get("tab") as Tab) : "manage";

  // Live status drives the header light and gates the RCON/Manage tabs.
  const liveStatus = useServerStatus(name ?? "", detail?.status);

  useEffect(() => {
    if (!name) {
      navigate("/servers");
      return;
    }
    // Reset the per-server log buffer when switching servers.
    setLogLines([]);
    setLogsCleared(false);
    logsSeededRef.current = false;
    (async () => {
      try {
        const [d, s] = await Promise.all([
          getJSON<ServerDetailData>(`/api/server/${name}`),
          getJSON<ManageServerData>(`/api/server/${name}/settings`),
        ]);
        setDetail(d);
        setSettings(s);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load server");
      }
    })();
  }, [name, navigate]);

  if (!name) {
    return null;
  }

  // Switching tabs only updates the query string — no page navigation/reload.
  const selectTab = (tab: Tab) => setSearchParams({ tab });

  return (
    <>
      <title>{name}</title>
      <Layout title="Manage Server">
        <div className="container-inner">
          <div className="medium-center">
            <div className="panel mb64 pb0 m0 flex flex-grow flex-column">
              <div className="flex flex-items-center" style={{ gap: 12, flexWrap: "wrap" }}>
                <h2 className="mb0">{name}</h2>
                <StatusLight status={liveStatus} showLabel />
              </div>

              {error ? <p className="red">{error}</p> : null}

              <nav className="server-tabs">
                {TABS.map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    className={`server-tab${tab === activeTab ? " active" : ""}`}
                    onClick={() => selectTab(tab)}
                  >
                    {TAB_LABELS[tab]}
                  </button>
                ))}
              </nav>

              <div className="tab-panel">
                {activeTab === "manage" &&
                  (detail ? (
                    <ManageTab
                      name={name}
                      ip={detail.ip}
                      port={detail.port}
                      status={liveStatus}
                      factorioVersion={detail.factorio_version}
                    />
                  ) : (
                    <p className="mb0">Loading…</p>
                  ))}
                {activeTab === "settings" &&
                  (settings ? (
                    <SettingsTab name={name} data={settings} />
                  ) : (
                    <p className="mb0">Loading settings…</p>
                  ))}
                {activeTab === "logs" && (
                  <LogsTab
                    name={name}
                    lines={logLines}
                    setLines={setLogLines}
                    cleared={logsCleared}
                    setCleared={setLogsCleared}
                    seededRef={logsSeededRef}
                  />
                )}
                {activeTab === "rcon" && <RconTab name={name} status={liveStatus} />}
                {activeTab === "mods" && <ModsTab name={name} />}
              </div>
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
