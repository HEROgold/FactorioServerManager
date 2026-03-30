import { useUser } from "@/contexts/UserContext";
import { useNavigate, useNavigation } from "react-router-dom";

export default function HomePage() {
  const user = useUser();
  const navigate = useNavigate();

  if (!user) {
    navigate("/login")
  } else {
    navigate("/servers")
  }
  return <></>
};
