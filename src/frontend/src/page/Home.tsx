import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "@/contexts/UserContext";

export default function HomePage() {
  const { user, loading } = useUser();
  const navigate = useNavigate();

  useEffect(() => {
    if (loading) {
      return;
    }
    navigate(user?.authenticated ? "/servers" : "/login");
  }, [loading, user, navigate]);

  return <></>;
}
