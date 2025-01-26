import React from 'react';
import './static/css/main.css';
import Footer from './components/footer.tsx';
import Header from './components/header.tsx';
import Navbar from './components/navbar.tsx';

function App() {
  return (
      <div className="App">
        <Header />
        <Navbar isAuthenticated={undefined} displayName={undefined} />
        <Footer />
      </div>
  );
}

export default App;
