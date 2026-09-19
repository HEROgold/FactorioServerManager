import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../../templates/Layout";
import StatusLight from "@/components/tags/StatusLight";
import ReachabilityLight from "@/components/tags/ReachabilityLight";
import LoginRequired from "@/components/LoginRequired";
import { getJSON, isUnauthorized } from "@/api";
import { useFeatureFlags } from "@/contexts/FeatureFlags";

export interface ServerSummary {
  name: string;
  port?: number | null;
  status?: string | null;
  reachable?: boolean | null;
}

interface DashboardResponse {
  servers: ServerSummary[];
}

interface PublicServer {
  name: string | null;
  status: string | null;
  address: string | null;
  reachable: boolean | null;
}

interface PublicResponse {
  servers: PublicServer[];
}

function Legend() {
  return (
    <div className="panel-inset-lighter mb12" style={{ fontSize: "0.85rem" }}>
      <div className="flex flex-wrap" style={{ gap: 20 }}>
        <span className="flex flex-items-center" style={{ gap: 6 }}>
          <StatusLight status="running" /> Status — running / stopped
        </span>
        <span className="flex flex-items-center" style={{ gap: 6 }}>
          <ReachabilityLight reachable /> Discoverability — listed in the public game browser
        </span>
      </div>
    </div>
  );
}

function ServerLink({ server }: { server: ServerSummary }) {
  return (
    <Link to={`/servers/${server.name}`} className="button button-ghost server-row">
      <StatusLight status={server.status} />
      <ReachabilityLight reachable={server.reachable} />
      <span>{server.name}</span>
    </Link>
  );
}

function PublicRow({ server }: { server: PublicServer }) {
  return (
    <div className="server-row" style={{ padding: "8px 0" }}>
      {server.status !== null ? <StatusLight status={server.status} /> : null}
      {server.reachable !== null ? <ReachabilityLight reachable={server.reachable} /> : null}
      <span>{server.name ?? "Hidden server"}</span>
      {server.address ? <span className="muted"> — {server.address}</span> : null}
    </div>
  );
}

// Fetches the caller's own servers (auth-gated) and the best-effort public
// server list in parallel.
function useOverviewData() {
  const [servers, setServers] = useState<ServerSummary[]>([]);
  const [publicServers, setPublicServers] = useState<PublicServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [unauthorized, setUnauthorized] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const data = await getJSON<DashboardResponse>("/api/dashboard/");
        setServers(data.servers ?? []);
      } catch (err) {
        if (isUnauthorized(err)) {
          setUnauthorized(true);
        } else {
          setError(err instanceof Error ? err.message : "Failed to load servers");
        }
      } finally {
        setLoading(false);
      }
    })();
    (async () => {
      try {
        const data = await getJSON<PublicResponse>("/api/servers/public");
        setPublicServers(data.servers ?? []);
      } catch {
        /* public list is best-effort; ignore failures */
      }
    })();
  }, []);

  return { servers, publicServers, loading, error, unauthorized };
}

function YourServersPanel({
  servers,
  loading,
  unauthorized,
  canCreate,
}: {
  servers: ServerSummary[];
  loading: boolean;
  unauthorized: boolean;
  canCreate: boolean;
}) {
  if (unauthorized) {
    return (
      <div className="panel-inset-lighter mb12">
        <LoginRequired message="Log in to view and manage your own servers." />
      </div>
    );
  }
  return (
    <div className="panel-inset-lighter mb12">
      {canCreate ? <Link to="/servers/create" className="button">Create Server</Link> : null}
      <div className="panel-inset-lighter mb12">
        <h3>Your servers</h3>
        {loading ? (
          <p className="mb0">Loading servers…</p>
        ) : servers.length === 0 ? (
          <p className="mb0">No servers yet. Create one to get started.</p>
        ) : (
          servers.map((server) => <ServerLink key={server.name} server={server} />)
        )}
      </div>
    </div>
  );
}

function PublicServersPanel({ servers }: { servers: PublicServer[] }) {
  return (
    <div className="panel-inset-lighter mb12">
      <h3>Public servers</h3>
      {servers.length === 0 ? (
        <p className="mb0">No public servers to show.</p>
      ) : (
        servers.map((server, i) => <PublicRow key={i} server={server} />)
      )}
    </div>
  );
}

export default function Overview() {
  const { servers, publicServers, loading, error, unauthorized } = useOverviewData();
  const { flags } = useFeatureFlags();

  return (
    <>
      <title>Dashboard</title>
      <Layout title="Dashboard">
        <div className="container-inner">
          {error ? (
            <div className="small-center">
              <p className="red">{error}</p>
            </div>
          ) : null}
          <div className="medium-center">
            <div className="panel mb64 pb0 m0 flex flex-grow flex-column">
              <h2>Server Overview</h2>
              <Legend />

              <YourServersPanel
                servers={servers}
                loading={loading}
                unauthorized={unauthorized}
                canCreate={flags.server_create}
              />

              <PublicServersPanel servers={publicServers} />
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
