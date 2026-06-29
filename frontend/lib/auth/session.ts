/**
 * auth/session.ts
 * 
 * Manages JWT session tokens. 
 */

const TOKEN_KEY = "rag_access_token";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function clearAuthToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function getRoles(): string[] {
  const token = getAuthToken();
  if (!token) return [];
  
  try {
    // JWT is header.payload.signature
    const parts = token.split(".");
    if (parts.length !== 3) return [];
    
    // Base64URL decode
    const payloadStr = atob(parts[1].replace(/-/g, "+").replace(/_/g, "/"));
    const payload = JSON.parse(payloadStr);
    
    const roles = payload.roles || [];
    if (Array.isArray(roles)) {
      return roles;
    }
    if (typeof roles === "string") {
      return roles.split(",").map(r => r.trim());
    }
    return [];
  } catch (e) {
    console.error("Failed to parse roles from token", e);
    return [];
  }
}
