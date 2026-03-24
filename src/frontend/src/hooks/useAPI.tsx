/**
 * Custom hooks for API operations
 */

import { useState, useEffect } from 'react';
import { apiClient, APIError } from '../api/client';

export function useServers() {
  const [servers, setServers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchServers = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.listServers();
      setServers(data);
    } catch (err) {
      setError(err instanceof APIError ? err.message : 'Failed to fetch servers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServers();
  }, []);

  return { servers, loading, error, refetch: fetchServers };
}

export function useServer(name: string) {
  const [server, setServer] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchServer = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.getServer(name);
      setServer(data);
    } catch (err) {
      setError(err instanceof APIError ? err.message : 'Failed to fetch server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (name) {
      fetchServer();
    }
  }, [name]);

  return { server, loading, error, refetch: fetchServer };
}

export function useServerMods(serverName: string) {
  const [mods, setMods] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMods = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.listServerMods(serverName);
      setMods(data.mods);
    } catch (err) {
      setError(err instanceof APIError ? err.message : 'Failed to fetch mods');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (serverName) {
      fetchMods();
    }
  }, [serverName]);

  return { mods, loading, error, refetch: fetchMods };
}
