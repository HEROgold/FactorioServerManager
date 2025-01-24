import React from 'react';

const Navbar = () => (
  <nav id="top" className="top-bar">
    <div className="top-bar-inner">
      <div className="sites links flex-items-baseline">
        <ul>
          <li><a href="/dashboard">Dashboard</a></li>
        </ul>
      </div>
      <div className="user-controls links flex flex-items-baseline flex-end">
        <div className="authenticated-controls">
          {/* Add logic to check if the user is authenticated */}
          <a href="/dashboard">User Name</a>
          <span className="separator separator-blue">|</span>
          <a href="/logout">Log out</a>
        </div>
      </div>
    </div>
  </nav>
);

export default Navbar;
