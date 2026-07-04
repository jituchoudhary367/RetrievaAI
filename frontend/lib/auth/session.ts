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

// NOTE: Storing the JWT in localStorage is a known XSS tradeoff for this MVP,
// allowing the browser to call FastAPI directly without a BFF-proxy pattern.
// Hardening to httpOnly cookies is a valid future architectural amendment.
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

export function getUserInfo(): { name: string; email?: string; avatarUrl: string; avatar_url: string } | null {
  const token = getAuthToken();
  if (!token) return null;
  
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payloadStr = atob(parts[1].replace(/-/g, "+").replace(/_/g, "/"));
    const payload = JSON.parse(payloadStr);
    const avatarUrl = payload.avatar_url || payload.picture || "";
    return {
      name: payload.name || payload.email || "User",
      email: payload.email || payload.sub,
      avatarUrl,
      avatar_url: avatarUrl,
    };
  } catch (e) {
    return null;
  }
}
