const DEFAULT_API_BASE_URL = "http://localhost:8000";

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE_URL
).replace(/\/$/, "");

export const WS_BASE_URL = (
  process.env.NEXT_PUBLIC_WS_BASE_URL ||
  API_BASE_URL.replace(/^http/, "ws")
).replace(/\/$/, "");

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export function wsUrl(path: string): string {
  return `${WS_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}
