import Container from "@/components/Container";
import Footer from "@/components/Footer";
import { Head } from "@/components/Head";
import Header from "@/components/header";
import Navbar from "@/components/Navbar";
import NoScript from "@/components/NoScript";
import { useUser } from "@/contexts/UserContext";
import type { ReactNode } from "react";

interface LayoutProps {
  children: ReactNode;
  title?: string;
}

export default function Layout({ children, title }: LayoutProps) {
  const { user } = useUser();

  return (
    <>
      <Head title={title} />
      <NoScript />
      <div className="content">
        <Navbar user={user} />
        <Header />
        <Container>{children}</Container>
      </div>
      <Footer />
    </>
  );
}
