import React from 'react';
import { ENDPOINTS } from '../../constants.ts';
import { NavLink } from 'react-router';

type Server = {
    name: string;
};

export default function ServerOverview() {
    const servers: Server[] = [];
    fetch(ENDPOINTS.ServerList)
        .then((response) => response.json())
        .then((data) => servers.push(...data));

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