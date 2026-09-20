import { Copyright } from "./Copyright"


export default function Footer() {
  return <>
    <footer className="footer">
      <div className="footer-inner panel">
        <FooterLinks />
        <Copyright />
      </div>
    </footer>
  </>
}

function FooterLinks() {
  return <>
    <div className="footer-links flex flex-wrap flex-center panel-inset m0">
      <a href="https://github.com/HEROgold/FactorioServerManager">Source code</a>
      <span className="separator">|</span>
      <a href="">Discord Server</a>
    </div>
  </>
}

