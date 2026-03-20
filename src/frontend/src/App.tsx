import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./index.css";

import { HomePage } from "./page/Home";
import FourZeroFour from "./page/404";
import Overview from "./page/server/Overview";
import Manage from "./page/server/Manage";
import Install from "./page/server/Install";

export function App() {
  return <>
    <BrowserRouter>
      <Routes>
        <Route index element={<HomePage />} />
        <Route path="/404" element={<FourZeroFour/>}/>
        <Route path="/servers" element={<Overview />} />
        <Route path="/servers/:name/" element={<Manage />} />
        <Route path="/servers/:name/create" element={<Install />} />
        {/* <Route path="/servers/:name/mods" element={<Mods />} /> */}
        {/* <Route path="/servers/:name/mods/install" element={<ModsInstall />} /> */}
        {/* <Route path="/servers/:name/mods/:modName" element={<ModsDetail />} /> */}
        {/* <Route path="/servers/:name/logs" element={<Logs />} /> */}
      </Routes>
    </BrowserRouter>
  </>
}

export default App;
