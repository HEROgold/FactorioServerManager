import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../../templates/Layout";
import StatusLight from "@/components/tags/StatusLight";
import { getJSON } from "@/api";

export interface ServerSummary {
  name: string;
  port?: number | null;
  status?: string | null;
}

interface DashboardResponse {
  servers: ServerSummary[];
}

function ServerLink({ server }: { server: ServerSummary }) {
  return (
    <Link to={`/servers/${server.name}`} className="button button-ghost server-row">
      <StatusLight status={server.status} />
      <span>{server.name}</span>
    </Link>
  );
}

export default function Overview() {
  const [servers, setServers] = useState<ServerSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await getJSON<DashboardResponse>("/api/dashboard/");
        setServers(data.servers ?? []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load servers");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <>
      <title>Dashboard</title>
      <Layout title="Dashboard">
        <div className="container-inner">
          <div id="flashed-messages" className="small-center">
            {error ? <p className="red">{error}</p> : null}
          </div>
          <div className="medium-center">
            <div className="panel mb64 pb0 m0 flex flex-grow flex-column">
              <h2>Server Overview</h2>
              <div className="panel-inset-lighter mb12">
                <Link to="/servers/create" className="button">Create Server</Link>
                <div className="panel-inset-lighter mb12">
                  <h3>Servers</h3>
                  {loading ? (
                    <p className="mb0">Loading servers…</p>
                  ) : servers.length === 0 ? (
                    <p className="mb0">No servers yet. Create one to get started.</p>
                  ) : (
                    servers.map((server) => <ServerLink key={server.name} server={server} />)
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
