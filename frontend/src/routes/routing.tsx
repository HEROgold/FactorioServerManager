
import React from 'react';
import { Routes, Route } from 'react-router';
import Login from './login.tsx';
import HomePage from './home.tsx';
import ServerOverview from './server/overview.tsx';
import ServerInstall from './server/install.tsx';
import ServerManager from './server/manager.tsx';

export default function Routing() {
    return (
        <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/home" element={<HomePage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<ServerOverview />} />
            <Route path="/server/install" element={<ServerInstall />} />
            <Route path="/server/manager" element={<ServerManager />} />
            <Route path="/server/overview" element={<ServerOverview />} />
        </Routes>
    )
}
