import React from 'react';
import './static/css/main.css';
import Footer from './components/footer.tsx';
import Header from './components/header.tsx';
import Navbar from './components/navbar.tsx';
import Routing from './routes/routing.tsx';

function App() {
  return (
      <div className="App">
        <Header />
        <Navbar />
        <Routing />
        <Footer />
      </div>
  );
}

export default App;
