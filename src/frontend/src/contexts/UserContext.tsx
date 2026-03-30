import React, { createContext, useContext, useEffect, useState } from "react";

export interface User {
  authenticated: boolean;
  display_name?: string;
}

interface UserContextValue {
  user: User | null;
  setUser: (u: User | null) => void;
  loading: boolean;
}

const defaultValue: UserContextValue = {
  user: null,
  setUser: () => {},
  loading: true,
};

const UserContext = createContext<UserContextValue>(defaultValue);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // If server injected a global `__USER__`, use it first
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    const injected = typeof window !== "undefined" ? (window.__USER__ as User | undefined) : undefined;
    if (injected) {
      setUser(injected);
      setLoading(false);
      return;
    }

    // Try fetching session info from a common endpoint. If it 404s or fails,
    // leave user as null (not authenticated).
    (async () => {
      try {
        const res = await fetch("/api/me", { credentials: "same-origin" });
        if (res.ok) {
          const data = await res.json();
          setUser({ authenticated: true, display_name: data.display_name ?? data.username ?? undefined });
        } else {
          setUser(null);
        }
      } catch (err) {
        setUser(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <UserContext.Provider value={{ user, setUser, loading }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  return useContext(UserContext);
}

export default UserContext;
