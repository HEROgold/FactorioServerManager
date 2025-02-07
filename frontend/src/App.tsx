import React from 'react';
import './static/css/main.css';
import Footer from './components/footer.tsx';
import Header from './components/header.tsx';
import Navbar from './components/navbar.tsx';
import Routing from './routes/routing.tsx';
import NoScript from './components/noscript.tsx';

function App() {
  return (
      <div className="App">
        <NoScript />
        <Header />
        <Navbar />
        <Routing />
        <Footer />
      </div>
  );
}

export default App;
