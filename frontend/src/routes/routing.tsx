
import React from 'react';
import { Routes, Route } from 'react-router';
import Login from './login.tsx';
import HomePage from './home.tsx';
import ServerOverview from './server/overview.tsx';

export default function Routing() {
    return (
        <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/home" element={<ServerOverview />} />
            <Route path="/login" element={<Login />} />
        </Routes>
    )
}
