import { Link, useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import Layout from "../../templates/Layout";
import { useAuth } from "../../hooks/useAuth";
import { useServer } from "../../hooks/useAPI";
import { apiClient, APIError } from "../../api/client";

function DeleteButton({ name }: { name: string }) {
  const navigate = useNavigate();

  const handleClick = async (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();

    if (confirm(`Are you sure you want to delete ${name}?`)) {
      try {
        await apiClient.deleteServer(name);
        navigate('/servers');
      } catch (error) {
        alert('Delete failed: ' + (error instanceof APIError ? error.message : 'Unknown error'));
      }
    }
  };

  return (
    <Link
      className="button button-red"
      to="/servers"
      onClick={handleClick}
    >
      Delete Server
    </Link>
  );
}

function ServerControls({ name, status }: { name: string; status: string }) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentStatus, setCurrentStatus] = useState(status);

  const handleAction = async (action: 'start' | 'stop' | 'restart') => {
    setIsLoading(true);
    setError(null);

    try {
      let result;
      switch (action) {
        case 'start':
          result = await apiClient.startServer(name);
          break;
        case 'stop':
          result = await apiClient.stopServer(name);
          break;
        case 'restart':
          result = await apiClient.restartServer(name);
          break;
      }
      setCurrentStatus(result.status);
    } catch (err) {
      setError(err instanceof APIError ? err.message : 'Action failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="panel-inset-lighter mb12 p12">
      <h3>Server Controls</h3>
      <div style={{ marginBottom: '12px' }}>
        Status: <strong>{currentStatus}</strong>
      </div>
      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={() => handleAction('start')}
          disabled={isLoading || currentStatus === 'running'}
          className="button"
        >
          Start
        </button>
        <button
          onClick={() => handleAction('stop')}
          disabled={isLoading || currentStatus !== 'running'}
          className="button"
        >
          Stop
        </button>
        <button
          onClick={() => handleAction('restart')}
          disabled={isLoading || currentStatus !== 'running'}
          className="button"
        >
          Restart
        </button>
      </div>
      {error && <p style={{ color: 'red', marginTop: '8px' }}>{error}</p>}
    </div>
  );
}

export default function Manage() {
  const { name } = useParams();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, authLoading, navigate]);

  const { server, loading, error, refetch } = useServer(name || '');

  if (!name) {
    navigate("/servers");
    return null;
  }

  if (authLoading || loading) {
    return (
      <Layout>
        <div className="container-inner">
          <div className="medium-center">
            <div className="panel mb64 pb0 m0 flex grow flex-column">
              <h2>{name}</h2>
              <p>Loading...</p>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="container-inner">
          <div className="medium-center">
            <div className="panel mb64 pb0 m0 flex grow flex-column">
              <h2>{name}</h2>
              <p style={{ color: 'red' }}>{error}</p>
              <Link to="/servers" className="button">
                Back to Servers
              </Link>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <title>{name}</title>
      <div className="container-inner">
        <div id="flashed-messages" className="small-center"></div>
        <div className="medium-center">
          <div className="panel mb64 pb0 m0 flex grow flex-column">
            <h2>{name}</h2>
            <div className="server-subnav" style={{ marginBottom: '12px' }}>
              <Link className="button button-ghost" to={`/servers/${name}/mods`}>
                Open Mod Manager
              </Link>
              <Link className="button button-ghost" to={`/servers/${name}/logs`}>
                View Logs
              </Link>
            </div>

            {server && <ServerControls name={name} status={server.status} />}

            <div className="panel-inset-lighter mb12 p12">
              <h3>Server Information</h3>
              {server && (
                <dl>
                  <dt>Version:</dt>
                  <dd>{server.version || 'Not installed'}</dd>
                  <dt>IP:</dt>
                  <dd>{server.ip || 'N/A'}</dd>
                  <dt>Port:</dt>
                  <dd>{server.port || 'N/A'}</dd>
                </dl>
              )}
            </div>

            <DeleteButton name={name} />
          </div>
        </div>
      </div>
    </Layout>
  );
}
