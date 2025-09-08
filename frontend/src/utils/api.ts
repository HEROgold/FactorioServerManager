import { ENDPOINTS } from "../constants";
import type { 
    ApiResponse, 
    Server, 
    User, 
    LoginCredentials, 
    LoginResponse, 
    FactorioVersions 
} from "../types/api";

export class ApiEndpoints {
    private async makeRequest<T = any>(endpoint: string, method: string = "GET", body?: any): Promise<ApiResponse<T>> {
        try {
            const response = await fetch(endpoint, {
                method,
                headers: {
                    "Content-Type": "application/json",
                },
                body: body ? JSON.stringify(body) : undefined,
            });

            if (!response.ok) {
                return {
                    error: `HTTP error! status: ${response.status}, message: ${response.statusText}`,
                    status: response.status
                };
            }

            const data = await response.json() as T;
            return {
                data,
                status: response.status
            };
        } catch (error) {
            return {
                error: error instanceof Error ? error.message : "Unknown error occurred",
                status: 0
            };
        }
    }

    // Server management endpoints
    async InstallServer(name: string, version: string, port: number): Promise<ApiResponse> {
        return this.makeRequest(ENDPOINTS.InstallServer(name), "POST", { version, port });
    }
    async FactorioVersions(): Promise<ApiResponse<FactorioVersions>> {
        return this.makeRequest(ENDPOINTS.FactorioVersions);
    }
    async LatestServerVersion(): Promise<ApiResponse<string>> {
        return this.makeRequest(ENDPOINTS.LatestServerVersion);
    }

    // Authentication endpoints
    async Login(credentials: LoginCredentials): Promise<ApiResponse<LoginResponse>> {
        return this.makeRequest(ENDPOINTS.Login, "POST", credentials);
    }
    async ValidateToken(token: string): Promise<ApiResponse<{ valid: boolean }>> {
        return this.makeRequest(ENDPOINTS.ValidateToken(token));
    }

    // Server listing and operations
    async ServerList(): Promise<ApiResponse<Server[]>> {
        return this.makeRequest(ENDPOINTS.ServerList);
    }
    async ServerDetails(id: string): Promise<ApiResponse<Server>> {
        return this.makeRequest(ENDPOINTS.ServerDetails(id));
    }
    async ServerStart(id: string): Promise<ApiResponse> {
        return this.makeRequest(ENDPOINTS.ServerStart(id), "POST");
    }
    async ServerStop(id: string): Promise<ApiResponse> {
        return this.makeRequest(ENDPOINTS.ServerStop(id), "POST");
    }
    async ServerRestart(id: string): Promise<ApiResponse> {
        return this.makeRequest(ENDPOINTS.ServerRestart(id), "POST");
    }
    async ServerDelete(id: string): Promise<ApiResponse> {
        return this.makeRequest(ENDPOINTS.ServerDelete(id), "DELETE");
    }
    async ServerSettings(id: string): Promise<ApiResponse> {
        return this.makeRequest(ENDPOINTS.ServerSettings(id));
    }

    // Mod management
    async ModsList(): Promise<ApiResponse<any[]>> {
        return this.makeRequest(ENDPOINTS.ModsList);
    }
    async ServerMods(id: string): Promise<ApiResponse<any[]>> {
        return this.makeRequest(ENDPOINTS.ServerMods(id));
    }

    // User endpoints
    async CurrentUser(): Promise<ApiResponse<User>> {
        return this.makeRequest(ENDPOINTS.CurrentUser);
    }
}

export const api = new ApiEndpoints();
export type { ApiResponse } from "../types/api";
