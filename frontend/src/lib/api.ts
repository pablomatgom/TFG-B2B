export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function authFetch(path: string, options: RequestInit = {}): Promise<Response> {
  // Import inline to avoid circular deps (auth.ts → api.ts would be circular)
  const { getToken } = await import("@/lib/auth");
  const token = getToken();
  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {}),
    },
  });
}