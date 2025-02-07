import React from 'react';
import { NavLink } from 'react-router';

export default function Navbar() {
    // TODO: Check JWT token to determine if user is authenticated
    const isAuthenticated = true;
    const displayName = 'User Name';

    return (
        <nav id="top" className="top-bar">
            <div className="top-bar-inner">
                <div className="sites as flex-items-baseline">
                    <ul>
                        <li><NavLink to="/dashboard">Dashboard</NavLink></li>
                    </ul>
                </div>
                <div className="user-controls as flex flex-items-baseline flex-end">
                    <div className="authenticated-controls">
                        {isAuthenticated ? (
                            <>
                                <NavLink to="/dashboard">{displayName}</NavLink>
                                <span className="separator separator-blue">|</span>
                                <NavLink to="/logout">Log out</NavLink>
                            </>
                        ) : (
                            <NavLink to="/login">Log in</NavLink>
                        )}
                    </div>
                </div>
            </div>
        </nav>
    );
};
