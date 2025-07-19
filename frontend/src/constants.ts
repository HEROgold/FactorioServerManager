const HOST = "http://api:3000";
const API = `${HOST}/api`;
const SERVERS = `${API}/servers`;
const USERS = `${API}/users`;

export const FACTORIO_LATEST_VERSION = "2.0.60";
export const DEFAULT_SERVER_PORT = 34197;

export const ENDPOINTS = {
    // Server management endpoints
    InstallServer: (name: string) => `${SERVERS}/create/${name}`,
    FactorioVersions: `${SERVERS}/versions`,
    LatestServerVersion: `${SERVERS}/versions/latest`,

    // Authentication endpoints
    Login: `${USERS}/auth/login`,
    ValidateToken: (token: string) => `${USERS}/auth/validate/${token}`,
    
    // Server listing and operations
    ServerList: `${SERVERS}`,
    ServerDetails: (id: string) => `${SERVERS}/${id}`,
    ServerStart: (id: string) => `${SERVERS}/${id}/start`,
    ServerStop: (id: string) => `${SERVERS}/${id}/stop`,
    ServerRestart: (id: string) => `${SERVERS}/${id}/restart`,
    ServerDelete: (id: string) => `${SERVERS}/${id}`,
    ServerSettings: (id: string) => `${SERVERS}/${id}/settings`,

    // WebSocket for server status
    ServerStatus: (id: string) => `${SERVERS}/${id}/ws`,

    // Mod management
    ModsList: `${API}/mods`,
    ServerMods: (id: string) => `${API}/servers/${id}/mods`,

    // User endpoints
    CurrentUser: `${USERS}/me`,
}