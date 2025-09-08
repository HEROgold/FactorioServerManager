import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router';
import { api } from '../../utils/api.ts';
import type { Server } from '../../types/api.ts';

export default function ServerOverview() {
    const [servers, setServers] = useState<Server[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchServers = async () => {
            setLoading(true);
            const response = await api.ServerList();
            
            if (response.error) {
                setError(`Failed to fetch servers: ${response.error}`);
            } else if (response.data) {
                setServers(response.data);
            }
            setLoading(false);
        };

        fetchServers();
    }, []);

    return (
        <div className="container-inner">
            <div id="flashed-messages" className="small-center"></div>
            <div className="medium-center">
                <div className="panel mb64 pb0 m0 flex-grow flex flex-column">
                    <h2>Server Overview</h2>
                    <div className="panel-inset-lighter mb12">
                        <NavLink to="/server/install" className="button">Create Server</NavLink>
                        <div className="panel-inset-lighter mb12">
                            <h3>Servers</h3>
                            {loading && <p>Loading servers...</p>}
                            {error && <p style={{ color: 'red' }}>{error}</p>}
                            {!loading && !error && servers.length === 0 && (
                                <p>No servers found. Create your first server!</p>
                            )}
                            {servers.map((server, index) => (
                                <a key={index} href={`/server/${server.name}`}>{server.name}</a>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}