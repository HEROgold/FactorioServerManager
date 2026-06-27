import { createBrowserRouter, Navigate, RouterProvider, useParams } from "react-router-dom";
import "./index.css";

import HomePage from "./page/Home";
import FourZeroFour from "./page/404";
import Overview from "./page/server/Overview";
import Install from "./page/server/Install";
import ServerDetail from "./page/server/ServerDetail";
import Download from "./page/Download";
import Login from "./page/login";
import { UserProvider } from "@/contexts/UserContext";

// Old per-feature routes now live as tabs on the unified detail page; redirect
// any bookmarked URLs to the matching tab.
function TabRedirect({ tab }: { tab: string }) {
  const { name } = useParams();
  return <Navigate to={`/servers/${name}?tab=${tab}`} replace />;
}

export function App() {
  const router = createBrowserRouter([
    { path: "/", element: <HomePage /> },
    { path: "/login", element: <Login /> },
    { path: "/servers", element: <Overview /> },
    { path: "/servers/create", element: <Install /> },
    { path: "/servers/:name", element: <ServerDetail /> },
    { path: "/servers/:name/logs", element: <TabRedirect tab="logs" /> },
    { path: "/servers/:name/rcon", element: <TabRedirect tab="rcon" /> },
    { path: "/servers/:name/mods", element: <TabRedirect tab="mods" /> },
    { path: "/downloads", element: <Download /> },
    { path: "*", element: <FourZeroFour /> },
  ]);

  return (
    <UserProvider>
      <RouterProvider router={router} />
    </UserProvider>
  );
}

export default App;
