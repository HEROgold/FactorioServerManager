import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./index.css";

import { HomePage } from "./page/Home";
import FourZeroFour from "./page/404";

export function App() {
  return <>
    <BrowserRouter>
      <Routes>
        <Route index element={<HomePage />} />
        <Route path="/404" element={<FourZeroFour/>}/>
      </Routes>
    </BrowserRouter>
  </>
}

export default App;
