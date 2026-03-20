import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

interface ServerInfo {
  name: string;
  ip: string;
  port: number;
  status: string;
}

interface StatusBoxProps {
  server: ServerInfo;
}

export default function StatusBox({ server }: StatusBoxProps) {
  const [currentStatus, setCurrentStatus] = useState<string>(server.status);
  useEffect(() => {
    const eventSource = new EventSource(`/api/server/${server.name}/status/stream`);

    eventSource.onmessage = (event: MessageEvent) => {
      setCurrentStatus(event.data);
    };

    eventSource.onerror = (err: Event) => {
      console.error("SSE connection failed:", err);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [server.name]);

  const handleAction = async (action: 'start' | 'stop' | 'restart'): Promise<void> => {
    try {
      const response = await fetch(`/api/server/${server.name}/${action}`, { 
        method: 'POST' 
      });
      if (!response.ok) throw new Error('Action failed');
    } catch (err) {
      console.error(`Fout bij ${action}:`, err);
    }
  };

  const copyToClipboard = (): void => {
    const text = `${server.ip}:${server.port}`;
    navigator.clipboard.writeText(text)
      .then(() => alert('IP:Port gekopieerd!'))
      .catch(err => console.error('Copy failed', err));
  };

  return (
    <div className="panel-inset-lighter mb12">
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <h3 style={{ marginRight: '10px' }}>Status</h3>
        
        <Link 
          to={`/server/${server.name}/logs`} 
          className="button button-ghost" 
          style={{ marginLeft: 'auto' }}
        >
          Logs
        </Link>
        
        <a 
          href={`/server/${server.name}/rcon`} 
          className="button button-ghost" 
          style={{ marginLeft: '8px' }}
          target="_blank" 
          rel="noreferrer"
        >
          RCON
        </a>

        <button 
          onClick={copyToClipboard}
          className="button"
          style={{ height: '50%', marginLeft: '8px' }}
        >
          Copy {server.ip}:{server.port}
        </button>
      </div>

      <div>
        <h4><strong>{currentStatus}</strong></h4>
      </div>

      <br />

      <div className="button-group">
        <button 
          onClick={() => handleAction('start')} 
          className="button"
        >
          Start
        </button>
        <button 
          onClick={() => handleAction('stop')} 
          className="button"
          style={{ marginLeft: '4px' }}
        >
          Stop
        </button>
        <button 
          onClick={() => handleAction('restart')} 
          className="button"
          style={{ marginLeft: '4px' }}
        >
          Restart
        </button>
      </div>
    </div>
  );
}
