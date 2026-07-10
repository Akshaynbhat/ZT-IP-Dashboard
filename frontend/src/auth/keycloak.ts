import Keycloak from "keycloak-js";

// Configure the Keycloak client instance
const keycloak = new Keycloak({
  url: "http://localhost:8080",
  realm: "zt-dashboard",
  clientId: "dashboard-frontend",
});

export async function initKeycloak(): Promise<boolean> {
  try {
    const authenticated = await keycloak.init({
      onLoad: "login-required",
      checkLoginIframe: false,
    });
    return authenticated;
  } catch (error) {
    console.error("Keycloak initialization failure:", error);
    return false;
  }
}

export function getToken(): string | undefined {
  return keycloak.token;
}

export function getUsername(): string {
  return (keycloak.tokenParsed as any)?.preferred_username ?? "unknown";
}

export function getUserId(): string {
  return keycloak.tokenParsed?.sub ?? "";
}

export function getRoles(): string[] {
  return (keycloak.tokenParsed as any)?.realm_access?.roles ?? [];
}

export function hasRole(role: string): boolean {
  return getRoles().includes(role);
}

export function logout(): void {
  keycloak.logout({ redirectUri: window.location.origin });
}

export default keycloak;
