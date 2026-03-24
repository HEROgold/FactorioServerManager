import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import Layout from "../../templates/Layout";
import { useAuth } from "../../hooks/useAuth";
import { useServers } from "../../hooks/useAPI";

interface Server {
  name: string;
  status: string;
  version: string | null;
  port: number | null;
  ip: string | null;
}

function ServerLink({ server }: { server: Server }) {
  const statusColor =
    server.status === 'running' ? 'green' :
    server.status === 'exited' ? 'red' :
    server.status === 'installing' ? 'blue' :
    'gray';

  return (
    <div className="panel-inset-lighter mb12 p12">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Link to={`/servers/${server.name}/`} style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
            {server.name}
          </Link>
          <div style={{ fontSize: '0.9rem', color: '#666' }}>
            Status: <span style={{ color: statusColor, fontWeight: 'bold' }}>{server.status}</span>
            {server.version && ` | Version: ${server.version}`}
            {server.ip && server.port && ` | ${server.ip}:${server.port}`}
          </div>
        </div>
        <div>
          <Link to={`/servers/${server.name}/`} className="button">
            Manage
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function Overview() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { servers, loading, error, refetch } = useServers();
  const navigate = useNavigate();
  const [serverName, setServerName] = useState("");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, authLoading, navigate]);

  if (authLoading || loading) {
    return (
      <Layout>
        <title>Dashboard</title>
        <div className="container-inner">
          <div className="medium-center">
            <div className="panel mb64 pb0 m0 flex grow flex-column">
              <h2>Server Overview</h2>
              <p>Loading...</p>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <title>Dashboard</title>
      <div className="container-inner">
        <div id="flashed-messages" className="small-center"></div>
        <div className="medium-center">
          <div className="panel mb64 pb0 m0 flex grow flex-column">
            <h2>Server Overview</h2>
            <div className="panel-inset-lighter mb12 p12">
              <div style={{ marginBottom: '16px' }}>
                <h3>Create New Server</h3>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <input
                    type="text"
                    placeholder="Server name"
                    value={serverName}
                    onChange={(e) => setServerName(e.target.value)}
                    style={{ flex: 1 }}
                  />
                  <Link
                    to={`/servers/${serverName}/create`}
                    className="button"
                    onClick={(e) => {
                      if (!serverName.trim()) {
                        e.preventDefault();
                        alert('Please enter a server name');
                      }
                    }}
                  >
                    Create Server
                  </Link>
                </div>
              </div>

              <div className="panel-inset-lighter mb12 p12">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <h3>Your Servers</h3>
                  <button onClick={refetch} className="button">
                    Refresh
                  </button>
                </div>

                {error && <p style={{ color: 'red' }}>{error}</p>}

                {servers.length === 0 ? (
                  <p>No servers yet. Create one to get started!</p>
                ) : (
                  servers.map((server) => (
                    <ServerLink key={server.name} server={server} />
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
