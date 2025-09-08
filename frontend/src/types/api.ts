// API response types
export interface ApiResponse<T = any> {
    data?: T;
    error?: string;
    status: number;
}

// Server related types
export interface Server {
    name: string;
    version: string;
    port: number;
    status: 'running' | 'stopped' | 'starting' | 'stopping';
    ip?: string;
}

export interface ServerSettings {
    name: string;
    description?: string;
    max_players?: number;
    visibility?: 'public' | 'lan' | 'friends';
    username?: string;
    password?: string;
    token?: string;
    game_password?: string;
    require_user_verification?: boolean;
    auto_pause?: boolean;
    only_admins_can_pause?: boolean;
    autosave_interval?: number;
    autosave_slots?: number;
    afk_autokick_interval?: number;
    auto_save_on_disconnect?: boolean;
    admins?: string[];
}

// User related types
export interface User {
    id: string;
    username: string;
    email?: string;
    servers: Server[];
}

export interface LoginCredentials {
    username: string;
    password: string;
}

export interface LoginResponse {
    token: string;
    user: User;
}

// Factorio version types
export interface FactorioVersions {
    core: {
        stable: string;
        experimental: string;
    };
    space_age: {
        stable: string;
        experimental: string;
    };
}
