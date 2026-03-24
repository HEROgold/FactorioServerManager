import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./index.css";

import { AuthProvider } from "./hooks/useAuth";
import { HomePage } from "./page/Home";
import FourZeroFour from "./page/404";
import Overview from "./page/server/Overview";
import Manage from "./page/server/Manage";
import Install from "./page/server/Install";
import LoginPage from "./page/login";
import ModManagerAPI from "./page/server/mods/ModManagerAPI";

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route index element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/404" element={<FourZeroFour/>}/>
          <Route path="/servers" element={<Overview />} />
          <Route path="/servers/:name/" element={<Manage />} />
          <Route path="/servers/:name/create" element={<Install />} />
          <Route path="/servers/:name/mods" element={<ModManagerAPI />} />
          {/* <Route path="/servers/:name/mods/install" element={<ModsInstall />} /> */}
          {/* <Route path="/servers/:name/mods/:modName" element={<ModsDetail />} /> */}
          {/* <Route path="/servers/:name/logs" element={<Logs />} /> */}
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
