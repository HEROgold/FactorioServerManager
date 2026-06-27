import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../../templates/Layout";
import StatusLight from "@/components/tags/StatusLight";
import ReachabilityLight from "@/components/tags/ReachabilityLight";
import LoginRequired from "@/components/LoginRequired";
import { getJSON, isUnauthorized } from "@/api";

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

export default function Overview() {
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

              <div className="panel-inset-lighter mb12">
                {unauthorized ? (
                  <LoginRequired message="Log in to view and manage your own servers." />
                ) : (
                  <>
                    <Link to="/servers/create" className="button">Create Server</Link>
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
                  </>
                )}
              </div>

              <div className="panel-inset-lighter mb12">
                <h3>Public servers</h3>
                {publicServers.length === 0 ? (
                  <p className="mb0">No public servers to show.</p>
                ) : (
                  publicServers.map((server, i) => <PublicRow key={i} server={server} />)
                )}
              </div>
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
