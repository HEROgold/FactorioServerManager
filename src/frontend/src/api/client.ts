/**
 * API client for Factorio Server Manager backend
 */

const API_BASE_URL = import.meta.env.BUN_PUBLIC_API_URL || 'http://localhost:8000';

class APIError extends Error {
  constructor(public status: number, message: string, public data?: any) {
    super(message);
    this.name = 'APIError';
  }
}

class APIClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.loadToken();
  }

  private loadToken(): void {
    this.token = localStorage.getItem('auth_token');
  }

  setToken(token: string | null): void {
    this.token = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new APIError(
        response.status,
        data.detail || response.statusText,
        data
      );
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // Authentication
  async login(email: string, password: string): Promise<{
    access_token: string;
    user_id: number;
    email: string;
    display_name: string;
  }> {
    const response = await this.request<any>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(response.access_token);
    return response;
  }

  async logout(): Promise<void> {
    await this.request('/api/auth/logout', { method: 'POST' });
    this.setToken(null);
  }

  async getCurrentUser(): Promise<{
    id: number;
    email: string;
    display_name: string;
  }> {
    return this.request('/api/auth/me');
  }

  // Servers
  async listServers(): Promise<Array<{
    name: string;
    status: string;
    version: string | null;
    port: number | null;
    ip: string | null;
  }>> {
    return this.request('/api/servers/');
  }

  async getServer(name: string): Promise<{
    name: string;
    status: string;
    version: string | null;
    port: number | null;
    ip: string | null;
  }> {
    return this.request(`/api/servers/${name}`);
  }

  async createServer(name: string, version: string): Promise<any> {
    return this.request('/api/servers/', {
      method: 'POST',
      body: JSON.stringify({ name, version }),
    });
  }

  async updateServer(name: string, version: string): Promise<any> {
    return this.request(`/api/servers/${name}`, {
      method: 'PUT',
      body: JSON.stringify({ version }),
    });
  }

  async deleteServer(name: string): Promise<void> {
    return this.request(`/api/servers/${name}`, {
      method: 'DELETE',
    });
  }

  async startServer(name: string): Promise<{ status: string }> {
    return this.request(`/api/servers/${name}/start`, {
      method: 'POST',
    });
  }

  async stopServer(name: string): Promise<{ status: string }> {
    return this.request(`/api/servers/${name}/stop`, {
      method: 'POST',
    });
  }

  async restartServer(name: string): Promise<{ status: string }> {
    return this.request(`/api/servers/${name}/restart`, {
      method: 'POST',
    });
  }

  async getServerStatus(name: string): Promise<{ status: string }> {
    return this.request(`/api/servers/${name}/status`);
  }

  async getServerLogs(name: string, previous: boolean = false): Promise<{ logs: string }> {
    const query = previous ? '?previous=true' : '';
    return this.request(`/api/servers/${name}/logs${query}`);
  }

  // Mods
  async searchMods(
    query: string = '',
    page: number = 1,
    pageSize: number = 12,
    serverName?: string
  ): Promise<any> {
    const params = new URLSearchParams({
      query,
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (serverName) {
      params.append('server_name', serverName);
    }
    return this.request(`/api/mods/search?${params.toString()}`);
  }

  async getModDetails(modName: string): Promise<any> {
    return this.request(`/api/mods/${modName}/details`);
  }

  async listServerMods(serverName: string): Promise<{
    mods: Array<{ name: string; enabled: boolean; version?: string }>;
  }> {
    return this.request(`/api/mods/${serverName}/mods`);
  }

  async installMod(
    serverName: string,
    modName: string,
    version?: string
  ): Promise<{ message: string }> {
    return this.request(`/api/mods/${serverName}/mods/install`, {
      method: 'POST',
      body: JSON.stringify({ mod_name: modName, version }),
    });
  }

  async batchInstallMods(
    serverName: string,
    mods: Array<{ mod_name: string; version?: string }>
  ): Promise<{ message: string }> {
    return this.request(`/api/mods/${serverName}/mods/batch-install`, {
      method: 'POST',
      body: JSON.stringify({ mods }),
    });
  }

  async toggleMod(
    serverName: string,
    modName: string,
    enabled: boolean
  ): Promise<{ name: string; enabled: boolean; version?: string }> {
    return this.request(`/api/mods/${serverName}/mods/toggle`, {
      method: 'PATCH',
      body: JSON.stringify({ mod_name: modName, enabled }),
    });
  }

  async uninstallMod(serverName: string, modName: string): Promise<void> {
    return this.request(`/api/mods/${serverName}/mods/${modName}`, {
      method: 'DELETE',
    });
  }

  async getInstalledMods(serverName: string): Promise<{
    installed_mods: Record<string, any[]>;
  }> {
    return this.request(`/api/mods/${serverName}/mods/installed`);
  }
}

export const apiClient = new APIClient();
export { APIError };
