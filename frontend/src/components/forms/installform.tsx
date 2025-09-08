import React, { useState, useEffect } from "react";
import { DEFAULT_SERVER_PORT, FACTORIO_LATEST_VERSION } from "../../constants.ts";
import { api } from "../../utils/api.ts";
import type { FactorioVersions } from "../../types/api.ts";

export type InstallFormProps = {
  name: string;
  version: string;
  port: number;
};

export default function InstallForm() {
  const serverName = "FactorioServer";

  const [name, setName] = useState(serverName);
  const [version, setVersion] = useState(FACTORIO_LATEST_VERSION);
  const [port, setPort] = useState(DEFAULT_SERVER_PORT);
  const [availableVersions, setAvailableVersions] = useState<FactorioVersions>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch available versions on component mount
  useEffect(() => {
    const fetchVersions = async () => {
      setLoading(true);
      const response = await api.FactorioVersions();
      if (response.error) {
        setError(`Failed to fetch versions: ${response.error}`);
      } else if (response.data) {
        setAvailableVersions(response.data);
      }
      setLoading(false);
    };

    fetchVersions();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;

    setIsSubmitting(true);

    const response = await api.InstallServer(name, version, port);
    
    if (response.error) {
      setError(`Failed to install server: ${response.error}`);
    } else {
      // Success - you might want to redirect or show success message
      console.log('Server installation started successfully');
      // Reset form or redirect
      setName(serverName);
      setVersion(FACTORIO_LATEST_VERSION);
      setPort(DEFAULT_SERVER_PORT);
    }
    
    setIsSubmitting(false);
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && (
        <div style={{ color: 'red', marginBottom: '10px' }}>
          {error}
        </div>
      )}
      
      <div>
        <label>Server Name</label>
        <input
          style={{ marginLeft: "5%", marginTop: "1%" }}
          type="text"
          name="name"
          value={name}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setName(e.currentTarget.value)}
          disabled={isSubmitting}
          required
        />
      </div>
      <br />
      
      <div>
        <label>Version</label>
        {loading ? (
          <span style={{ marginLeft: "5%" }}>Loading versions...</span>
        ) : (
          <select
            style={{ marginLeft: "5%", marginTop: "1%" }}
            name="version"
            value={version}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setVersion(e.target.value)}
            disabled={isSubmitting}
          >
            <option value={FACTORIO_LATEST_VERSION}>Latest ({FACTORIO_LATEST_VERSION})</option>
            {availableVersions && (
              <>
                <optgroup label="Core - Stable">
                  <option value={availableVersions.core.stable}>
                    {availableVersions.core.stable}
                  </option>
                </optgroup>
                <optgroup label="Core - Experimental">
                  <option value={availableVersions.core.experimental}>
                    {availableVersions.core.experimental}
                  </option>
                </optgroup>
                <optgroup label="Space Age - Stable">
                  <option value={availableVersions.space_age.stable}>
                    {availableVersions.space_age.stable}
                  </option>
                </optgroup>
                <optgroup label="Space Age - Experimental">
                  <option value={availableVersions.space_age.experimental}>
                    {availableVersions.space_age.experimental}
                  </option>
                </optgroup>
              </>
            )}
          </select>
        )}
      </div>
      <br />
      
      <div>
        <label>Port</label>
        <input
          style={{ marginLeft: "5%", marginTop: "1%" }}
          type="number"
          name="port"
          value={port}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPort(parseInt(e.target.value) || DEFAULT_SERVER_PORT)}
          disabled={isSubmitting}
          min="1024"
          max="65535"
          required
        />
      </div>
      <br />
      
      <button 
        type="submit" 
        disabled={isSubmitting || loading}
        style={{ 
          opacity: isSubmitting || loading ? 0.6 : 1,
          cursor: isSubmitting || loading ? 'not-allowed' : 'pointer'
        }}
      >
        {isSubmitting ? 'Installing...' : 'Install Server'}
      </button>
    </form>
  );
}
