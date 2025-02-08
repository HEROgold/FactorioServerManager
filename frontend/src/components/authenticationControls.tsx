import React from "react";
import { NavLink } from "react-router";

function handleLogout() {
    localStorage.removeItem("token");
    window.location.reload();
}

export default function AuthenticationControls(p: { isAuthenticated: boolean }) {
    return (
        <div className="authenticated-controls">
            {p.isAuthenticated ? (
                <NavLink to="/logout" onClick={handleLogout}>Log out</NavLink>
            ) : (
                <NavLink to="/login">Log in</NavLink>
            )}
        </div>
    );
}
