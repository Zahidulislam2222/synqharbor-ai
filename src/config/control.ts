export const control = {
  apiPrefix: process.env.NEXT_PUBLIC_API_PREFIX ?? "/api/v1",
  pollMilliseconds: 3000,
  requestTimeoutMilliseconds: 15000,
  limits: { name: 80, title: 100, text: 4000, sourceBytes: 4000, passwordMin: 12, passwordMax: 128 },
  endpoints: {
    session: "/auth/session", register: "/auth/register", login: "/auth/login",
    logout: "/auth/logout", workspaces: "/workspaces", capabilities: "/capabilities",
    acceptInvitation: "/invitations/accept",
  },
} as const;

if (!/^\/[a-zA-Z0-9/_-]+$/.test(control.apiPrefix))
  throw new Error("API prefix must be a same-origin path");
