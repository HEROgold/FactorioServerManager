import Container from "@/components/Container";
import Footer from "@/components/Footer";
import { Head } from "@/components/Head";
import Header from "@/components/header";
import type { User } from "@/components/Navbar";
import Navbar from "@/components/Navbar";
import NoScript from "@/components/NoScript";
import type { ReactNode } from "react";

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
      <NoScript />
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
