import { useEffect, useRef, useState } from "react";
import type { MutableRefObject } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import type { NavigateFunction } from "react-router-dom";
import Layout from "@/templates/Layout";
import StatusLight from "@/components/tags/StatusLight";
import LoginRequired from "@/components/LoginRequired";
import { useServerStatus } from "@/hooks/useServerStatus";
import { useFeatureFlags } from "@/contexts/FeatureFlags";
import type { FeatureFlags } from "@/types/featureFlags";
import { getJSON, isUnauthorized } from "@/api";
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

// Tabs gated behind a feature flag. A tab with no entry is always shown; one
// with a predicate shows only when the predicate holds for the current flags.
const TAB_ENABLED: Partial<Record<Tab, (flags: FeatureFlags) => boolean>> = {
  mods: (flags) => flags.Mods.enabled,
  rcon: (flags) => flags.rcon_console,
};

interface LogBufferState {
  logLines: string[];
  setLogLines: React.Dispatch<React.SetStateAction<string[]>>;
  logsCleared: boolean;
  setLogsCleared: (value: boolean) => void;
  logsSeededRef: MutableRefObject<boolean>;
}

// Log buffer lives here (not in LogsTab) so a manual "Clear" survives tab
// switches — LogsTab unmounts when you leave the Logs tab. Reset whenever the
// active server changes.
function useLogBuffer(name: string | undefined): LogBufferState {
  const [logLines, setLogLines] = useState<string[]>([]);
  const [logsCleared, setLogsCleared] = useState(false);
  const logsSeededRef = useRef(false);

  useEffect(() => {
    setLogLines([]);
    setLogsCleared(false);
    logsSeededRef.current = false;
  }, [name]);

  return { logLines, setLogLines, logsCleared, setLogsCleared, logsSeededRef };
}

function useServerDetailData(name: string | undefined, navigate: NavigateFunction) {
  const [detail, setDetail] = useState<ServerDetailData | null>(null);
  const [settings, setSettings] = useState<ManageServerData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [unauthorized, setUnauthorized] = useState(false);

  useEffect(() => {
    if (!name) {
      navigate("/servers");
      return;
    }
    (async () => {
      try {
        const [d, s] = await Promise.all([
          getJSON<ServerDetailData>(`/api/server/${name}`),
          getJSON<ManageServerData>(`/api/server/${name}/settings`),
        ]);
        setDetail(d);
        setSettings(s);
      } catch (err) {
        if (isUnauthorized(err)) {
          setUnauthorized(true);
        } else {
          setError(err instanceof Error ? err.message : "Failed to load server");
        }
      }
    })();
  }, [name, navigate]);

  return { detail, settings, error, unauthorized };
}

function TabNav({
  tabs,
  activeTab,
  onSelect,
}: {
  tabs: readonly Tab[];
  activeTab: Tab;
  onSelect: (tab: Tab) => void;
}) {
  return (
    <nav className="server-tabs">
      {tabs.map((tab) => (
        <button
          key={tab}
          type="button"
          className={`server-tab${tab === activeTab ? " active" : ""}`}
          onClick={() => onSelect(tab)}
        >
          {TAB_LABELS[tab]}
        </button>
      ))}
    </nav>
  );
}

function TabContent({
  activeTab,
  name,
  detail,
  settings,
  liveStatus,
  logState,
}: {
  activeTab: Tab;
  name: string;
  detail: ServerDetailData | null;
  settings: ManageServerData | null;
  liveStatus: string;
  logState: LogBufferState;
}) {
  if (activeTab === "manage") {
    return detail ? (
      <ManageTab
        name={name}
        ip={detail.ip}
        port={detail.port}
        status={liveStatus}
        factorioVersion={detail.factorio_version}
      />
    ) : (
      <p className="mb0">Loading…</p>
    );
  }
  if (activeTab === "settings") {
    return settings ? <SettingsTab name={name} data={settings} /> : <p className="mb0">Loading settings…</p>;
  }
  if (activeTab === "logs") {
    return (
      <LogsTab
        name={name}
        lines={logState.logLines}
        setLines={logState.setLogLines}
        cleared={logState.logsCleared}
        setCleared={logState.setLogsCleared}
        seededRef={logState.logsSeededRef}
      />
    );
  }
  if (activeTab === "rcon") {
    return <RconTab name={name} status={liveStatus} />;
  }
  return <ModsTab name={name} />;
}

// The active tab: a bookmarked/redirected `?tab=<hidden>` falls back to "manage".
function useActiveTab(visibleTabs: readonly Tab[], searchParams: URLSearchParams): Tab {
  const requestedTab = searchParams.get("tab");
  return isTab(requestedTab) && visibleTabs.includes(requestedTab) ? requestedTab : "manage";
}

function UnauthorizedView({ name }: { name: string }) {
  return (
    <>
      <title>{name}</title>
      <Layout title="Manage Server">
        <div className="container-inner">
          <div className="medium-center">
            <LoginRequired message="Please log in to manage this server." />
          </div>
        </div>
      </Layout>
    </>
  );
}

interface ServerDetailBodyProps {
  name: string;
  error: string | null;
  liveStatus: string;
  visibleTabs: readonly Tab[];
  activeTab: Tab;
  onSelectTab: (tab: Tab) => void;
  detail: ServerDetailData | null;
  settings: ManageServerData | null;
  logState: LogBufferState;
}

function ServerDetailPanel({
  name,
  error,
  liveStatus,
  visibleTabs,
  activeTab,
  onSelectTab,
  detail,
  settings,
  logState,
}: ServerDetailBodyProps) {
  return (
    <div className="panel mb64 pb0 m0 flex flex-grow flex-column">
      <div className="flex flex-items-center" style={{ gap: 12, flexWrap: "wrap" }}>
        <h2 className="mb0">{name}</h2>
        <StatusLight status={liveStatus} showLabel />
      </div>

      {error ? <p className="red">{error}</p> : null}

      <TabNav tabs={visibleTabs} activeTab={activeTab} onSelect={onSelectTab} />

      <div className="tab-panel">
        <TabContent
          activeTab={activeTab}
          name={name}
          detail={detail}
          settings={settings}
          liveStatus={liveStatus}
          logState={logState}
        />
      </div>
    </div>
  );
}

function ServerDetailBody(props: ServerDetailBodyProps) {
  return (
    <>
      <title>{props.name}</title>
      <Layout title="Manage Server">
        <div className="container-inner">
          <div className="medium-center">
            <ServerDetailPanel {...props} />
          </div>
        </div>
      </Layout>
    </>
  );
}

export default function ServerDetail() {
  const { name } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { detail, settings, error, unauthorized } = useServerDetailData(name, navigate);
  const logState = useLogBuffer(name);
  const { flags } = useFeatureFlags();

  // Tabs the current flags allow. Gated-off tabs disappear from the bar.
  const visibleTabs = TABS.filter((tab) => !TAB_ENABLED[tab] || TAB_ENABLED[tab]!(flags));
  const activeTab = useActiveTab(visibleTabs, searchParams);

  // Live status drives the header light and gates the RCON/Manage tabs.
  const liveStatus = useServerStatus(name ?? "", detail?.status);

  if (!name) {
    return null;
  }

  if (unauthorized) {
    return <UnauthorizedView name={name} />;
  }

  return (
    <ServerDetailBody
      name={name}
      error={error}
      liveStatus={liveStatus}
      visibleTabs={visibleTabs}
      activeTab={activeTab}
      // Switching tabs only updates the query string — no page navigation/reload.
      onSelectTab={(tab) => setSearchParams({ tab })}
      detail={detail}
      settings={settings}
      logState={logState}
    />
  );
}
