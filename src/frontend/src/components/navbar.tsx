import React from 'react';
import { NavLink } from 'react-router';

function Navbar({ isAuthenticated, displayName }) {
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

export default Navbar;
