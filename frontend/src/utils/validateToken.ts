import { ENDPOINTS } from "../constants.ts";

export function removeAuthToken(): void {
    localStorage.removeItem('token');
}

export default function validateToken(): boolean {
    const token = localStorage.getItem('token');
    if (!token) {
        removeAuthToken();
        return false;
    }
    fetch(ENDPOINTS.ValidateToken(token)).then(response => {
        if (!response.ok) {
            removeAuthToken();
        }
        return false;
    });
    return true;
}
