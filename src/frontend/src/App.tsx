import React from 'react';
import './static/css/main.css';
import Footer from './components/footer.tsx';
import Header from './components/header.tsx';
import Navbar from './components/navbar.tsx';
import Login from './routes/login.tsx';
import HomePage from './routes/home.tsx';

function App() {
  return (
      <div className="App">
        <Header />
        <Navbar isAuthenticated={undefined} displayName={undefined} />
        <HomePage />
        <Login />
        <Footer />
      </div>
  );
}

export default App;
