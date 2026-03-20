import Header from "@/templates/header";
import Footer from "@/templates/footer";
import Navbar, { type User } from "@/templates/navbar";
import type { ReactNode } from "react";
import { Head } from "./Head";
import Container from "@/templates/Container";

interface LayoutProps {
  children: ReactNode;
  title?: string;
}


export default function Layout({ children }: LayoutProps) {
  const user: User = {
    authenticated: true,
    display_name: "HEROgold"
  }

  return (
    <html lang="en">
      <Head />
      <body>
        <div className="content">
          <Navbar user={user}/>
          <Header />
          <Container>
            {children}
          </Container>
        </div>
        <Footer />
      </body>
    </html>
  );
};
