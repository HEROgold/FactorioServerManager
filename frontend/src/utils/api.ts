import { ENDPOINTS } from "../constants";

export class ApiEndpoints {
    private makeRequest(endpoint: string, method: string = "GET", body?: any): Response {
        const result = fetch(endpoint, {
            method,
            headers: {
                "Content-Type": "application/json",
            },
            body: body ? JSON.stringify(body) : undefined,
        });

        result.then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}, message: ${response.statusText}`);
            }
            return response;
        });
        throw new Error("invalid response");
    }

    // Server management endpoints
    InstallServer(name: string) {
        return this.makeRequest(ENDPOINTS.InstallServer(name));
    }
    FactorioVersions() {
        return this.makeRequest(ENDPOINTS.FactorioVersions);
    }
    LatestServerVersion() {
        return this.makeRequest(ENDPOINTS.LatestServerVersion);
    }

    // Authentication endpoints
    Login() {
        return this.makeRequest(ENDPOINTS.Login);
    }
    ValidateToken(token: string) {
        return this.makeRequest(ENDPOINTS.ValidateToken(token));
    }

    // Server listing and operations
    ServerList() {
        return this.makeRequest(ENDPOINTS.ServerList);
    }
    ServerDetails(id: string) {
        return this.makeRequest(ENDPOINTS.ServerDetails(id));
    }
    ServerStart(id: string) {
        return this.makeRequest(ENDPOINTS.ServerStart(id));
    }
    ServerStop(id: string) {
        return this.makeRequest(ENDPOINTS.ServerStop(id));
    }
    ServerRestart(id: string) {
        return this.makeRequest(ENDPOINTS.ServerRestart(id));
    }
    ServerDelete(id: string) {
        return this.makeRequest(ENDPOINTS.ServerDelete(id));
    }
    ServerSettings(id: string) {
        return this.makeRequest(ENDPOINTS.ServerSettings(id));
    }

    // WebSocket for server status
    ServerStatus(id: string) {
        return this.makeRequest(ENDPOINTS.ServerStatus(id));
    }

    // Mod management
    ModsList() {
        return this.makeRequest(ENDPOINTS.ModsList);
    }
    ServerMods(id: string) {
        return this.makeRequest(ENDPOINTS.ServerMods(id));
    }

    // User endpoints
    CurrentUser() {
        return this.makeRequest(ENDPOINTS.CurrentUser);
    }
}
export const api = new ApiEndpoints();
