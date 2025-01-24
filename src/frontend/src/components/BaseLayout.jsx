import React from 'react';
import Navbar from './Navbar';
import Header from './Header';
import Footer from './Footer';

const BaseLayout = ({ children }) => (
  <div className="content">
    <Navbar />
    <Header />
    <div className="container">
      {children}
    </div>
    <Footer />
  </div>
);

export default BaseLayout;
