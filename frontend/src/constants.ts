export const ENDPOINTS = {
    InstallServer: (name: string) => `/api/server/install/${name}`,
    FactorioVersions: `/api/server/version/all`,
    LatestServerVersion: `/api/server/version/latest`,
    Login: `/api/auth/login`,
    ValidateToken: (token: string) => `/api/auth/validate/${token}`,
    ServerList: "/api/server/list",
}