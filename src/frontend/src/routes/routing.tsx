
import React from 'react';
import { Routes, Route } from 'react-router';
import Login from './login.tsx';
import HomePage from './home.tsx';

function Routing() {
    return (
        <Routes>
            <Route path= "/" element = {<HomePage />} />
            <Route path = "/login" element = {<Login />} />
        </Routes>
    )
}

export default Routing;
