import React from 'react';
import { NavLink } from 'react-router';

function Footer() {
    return (
        <footer className="footer">
            <div className="footer-inner panel">
                <div className="footer-links flex flex-wrap flex-center panel-inset m0">
                    <a href="https://github.com/HEROgold/FactorioServerManager">Source code</a>
                    <span className="separator">|</span>
                    <NavLink to="/discord"/>
                    <a href="">Discord Server</a>
                </div>
                <div className="footer-rocket panel-inset m0 p0">
                    <div id="rocket" className="rocket"></div>
                    <div className="shadow-overlay"></div>
                    <div className="shadow-overlay-bottom"></div>
                </div>
                <div className="footer-copyright panel-inset m0">
                    <p>Disclaimer: This website is not associated with Factorio. We solely use their API to fulfill the required functionality of this website.</p>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
