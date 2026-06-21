const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Role = "viewer" | "operator";
export type Interaction = { id: string; direction: string; kind: string; content: string; created_at: string };
export type Run = { run_id: string; trigger: string; provider: string; model?: string; latency_ms: number; estimated_cost_usd: number; fallback: boolean; evidence: string[]; decision: { action: string; rationale: string[]; confidence?: number; requires_human_review?: boolean } };
export type Lead = { id: string; name: string; email: string; company: string; company_website?: string; job_title: string; challenge: string; status: string; attendance: string; demo_interest: boolean; eligible_for_processing: boolean; fit_score: number; intent_score: number; engagement_score: number; total_score: number; tier: string; enrichment?: Record<string, string>; interactions: Interaction[]; runs: Run[]; meeting_id?: string };
export type Dashboard = { metrics: Record<string, number>; leads: Lead[] };
export type Slot = { id: string; starts_at: string; duration_minutes: number };
export type Session = { username: string; role: Role };

async function call<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, { ...options, credentials: "include", headers: { "Content-Type": "application/json", ...(options?.headers || {}) }, cache: "no-store" });
  if (!res.ok) { const error = await res.json().catch(() => ({})); throw new Error(error.detail || "Não foi possível concluir a operação."); }
  return res.status === 204 ? (undefined as T) : res.json();
}
export const api = {
  session: () => call<Session>("/auth/session"),
  login: (username: string, password: string) => call<Session>("/auth/session", { method: "POST", body: JSON.stringify({ username, password }) }),
  logout: () => call<void>("/auth/session", { method: "DELETE" }),
  dashboard: () => call<Dashboard>("/dashboard"),
  createLead: (body: object) => call<Lead>("/leads", { method: "POST", body: JSON.stringify(body) }),
  reply: (id: string, content: string) => call<Lead>(`/leads/${id}/reply`, { method: "POST", body: JSON.stringify({ content }) }),
  attendance: (id: string, attended: boolean, demo_interest: boolean) => call<Lead>(`/leads/${id}/attendance`, { method: "POST", body: JSON.stringify({ attended, demo_interest }) }),
  slots: () => call<Slot[]>("/slots"),
  book: (lead_id: string, slot_id: string) => call("/meetings", { method: "POST", body: JSON.stringify({ lead_id, slot_id }) }),
  erase: (id: string) => call<void>(`/leads/${id}`, { method: "DELETE" }),
};