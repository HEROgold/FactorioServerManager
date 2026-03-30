import { createBrowserRouter, RouterProvider } from "react-router-dom";
import "./index.css";

import HomePage from "./page/Home";
import FourZeroFour from "./page/404";
import Overview from "./page/server/Overview";
import Manage from "./page/server/Manage";
import Install from "./page/server/Install";
import Login from "./page/login";
import { UserProvider } from "@/contexts/UserContext";

export function App() {
  const router = createBrowserRouter([
    { path: "/", element: <HomePage /> },
    { path: "/404", element: <FourZeroFour /> },
    { path: "/servers", element: <Overview /> },
    { path: "/servers/:name/", element: <Manage /> },
    { path: "/servers/:name/create", element: <Install /> },
    { path: "/login", element: <Login /> },
    // TODO: add loader/action functions for routes that need them
  ]);

  return (
    <>
      <UserProvider>
        <RouterProvider router={router} />
      </UserProvider>
    </>
  );
}

export default App;
