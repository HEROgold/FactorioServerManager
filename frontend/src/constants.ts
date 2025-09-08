const HOST = "http://api:3000";
const API = `${HOST}/api`;
const SERVERS = `${API}/server`;
const USERS = `${API}/users`;

export const FACTORIO_LATEST_VERSION = "2.0.60";
export const DEFAULT_SERVER_PORT = 34197;

export const ENDPOINTS = {
    // Server management endpoints
    InstallServer: (name: string) => `${SERVERS}/manage/create`,
    FactorioVersions: `${SERVERS}/version/all`,
    LatestServerVersion: `${SERVERS}/version/latest`,

    // Authentication endpoints
    Login: `${USERS}/auth/login`,
    ValidateToken: (token: string) => `${USERS}/auth/validate/${token}`,
    
    // Server listing and operations
    ServerList: `${SERVERS}/list`,
    ServerDetails: (id: string) => `${SERVERS}/${id}`,
    ServerStart: (id: string) => `${SERVERS}/manage/start`,
    ServerStop: (id: string) => `${SERVERS}/manage/stop`,
    ServerRestart: (id: string) => `${SERVERS}/manage/restart`,
    ServerDelete: (id: string) => `${SERVERS}/manage/delete`,
    ServerSettings: (id: string) => `${SERVERS}/${id}/settings`,

    // WebSocket for server status
    ServerStatus: (id: string) => `${SERVERS}/manage/status`,

    // Mod management
    ModsList: `${API}/mods`,
    ServerMods: (id: string) => `${API}/servers/${id}/mods`,

    // User endpoints
    CurrentUser: `${USERS}/me`,
}