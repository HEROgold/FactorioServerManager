import React from "react";
import validateToken from "../utils/validateToken.ts";
import AuthenticationControls from "./authenticationControls.tsx";
import NavRoute from "./navRoute.tsx";

export default function Navbar() {
  // TODO: Check JWT token to determine if user is authenticated
  const isAuthenticated = validateToken();
  const routes = ["Home", "Dashboard"];

  return (
    <nav id="top" className="top-bar">
      <div className="top-bar-inner">
        <div className="sites links flex-items-baseline">
          <ul>
            {routes.map((text, index) => (
              <NavRoute key={index} text={text} index={index} total={routes.length} />
            ))}
          </ul>
        </div>
        <div className="user-controls links flex flex-items-baseline flex-end">
          <AuthenticationControls isAuthenticated={isAuthenticated} />
        </div>
      </div>
    </nav>
  );
}
