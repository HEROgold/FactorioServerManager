import React from 'react';
import { ENDPOINTS } from '../../constants';

type Server = {
    name: string;
};

export default function ServerOverview() {
    const servers: Server[] = [];
    fetch(ENDPOINTS.ServerList)
        .then((response) => response.json())
        .then((data) => servers.push(...data));

    return (
        <div class="container-inner">
            <div id="flashed-messages" class="small-center"></div>
            <div class="medium-center">
                <div class="panel mb64 pb0 m0 flex-grow flex flex-column">
                    <h2>Server Overview</h2>
                    <div class="panel-inset-lighter mb12">
                        <a href="{{url_for('server.install', name='FactorioServer')}}" class="button">Create Server</a>
                        <div class="panel-inset-lighter mb12">
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