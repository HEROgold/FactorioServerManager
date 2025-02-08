import React from "react";
import { NavLink } from "react-router";



export default function NavRoute(p: { text: string; index: number, total: number }) {
  const { text, index, total } = p;

  return (
    <>
      <li key={index}>
        <NavLink
          to={`/${text.toLowerCase()}`}
          className={({ isActive }) => (isActive ? "sites-current" : "")}
        >
          {text}
        </NavLink>
      </li>
      {index < total - 1 && (
        <span className="separator separator-blue">|</span>
      )}
    </>
  );
}
