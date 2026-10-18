import { control } from "@/config/control";

export class ApiError extends Error {
  constructor(public readonly code: string, public readonly status: number) { super(code); }
}

export async function request<T>(path: string, csrf: string, body?: unknown, method?: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(control.apiPrefix + path, {
      method: method ?? (body === undefined ? "GET" : "POST"),
      credentials: "same-origin", cache: "no-store",
      signal: AbortSignal.timeout(control.requestTimeoutMilliseconds),
      headers: body === undefined ? {} : { "Content-Type": "application/json", "X-CSRF-Token": csrf },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch { throw new ApiError("unavailable", 0); }
  if (!response.ok) {
    const error = await response.json().catch(() => ({})) as { detail?: { code?: string } };
    throw new ApiError(error.detail?.code ?? "unavailable", response.status);
  }
  if (response.status === 204) return undefined as T;
  try { return await response.json() as T; }
  catch { throw new ApiError("unavailable", 0); }
}

export interface Person { id: string; name: string; email: string }
export interface WorkspaceRecord { id: string; name: string; role: string }
export interface ControlTask {
  id: string; title: string; description: string; criteria: string[]; status: string;
  version: number; revision: number; content_hash: string | null; artifact_id: string | null;
  clientApproved: boolean; developerApproved: boolean;
}
export interface WorkspaceState {
  workspace: WorkspaceRecord; tasks: ControlTask[];
  members: { id: string; name: string; role: string }[];
  messages: { id: string; name: string; text: string }[];
  activity: { id: string; action: string; actor: string }[];
}
export interface RepositoryScope { target: string; profile: string; name: string; specification: string; files: string[] }
export interface SourceRecord { id: string; name: string; text: string; content_hash: string }
export interface RunRecord {
  id: string; task_id: string; status: string; mode: string; attempt: number;
  error_code: string | null; evidence: Record<string, unknown>;
  events: { sequence: number; action: string }[];
}
export interface Receipt { id: string; task_id: string; content_hash: string; destination: string;
  release: { status: string; error_code: string | null; receipt: Record<string, unknown> } | null }
export interface Capabilities {
  inference_configured: boolean; runner_configured: boolean;
  fixtures: { id: string; name: string; specification: string }[];
}
