export interface ProblemDetail {
  type?: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  [key: string]: unknown;
}

export class ApiError extends Error {
  status: number;
  problem: ProblemDetail;

  constructor(problem: ProblemDetail) {
    super(problem.title || `HTTP ${problem.status}`);
    this.status = problem.status;
    this.problem = problem;
  }
}

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface ApiFetchOpts {
  auth?: boolean;
}

async function attempt(path: string, init: RequestInit) {
  const url = path.startsWith("http") ? path : `${BASE}${path}`;
  const headers = new Headers(init.headers);
  if (!headers.has("Accept")) headers.set("Accept", "application/json");
  if (!headers.has("X-Requested-With"))
    headers.set("X-Requested-With", "XMLHttpRequest");
  if (init.body && !headers.has("Content-Type"))
    headers.set("Content-Type", "application/json");

  return fetch(url, {
    ...init,
    headers,
    credentials: "include",
  });
}

async function refresh() {
  const res = await fetch(`${BASE}/api/v1/auth/refresh/`, {
    method: "POST",
    credentials: "include",
    headers: { "X-Requested-With": "XMLHttpRequest" },
  });
  return res.ok;
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  opts: ApiFetchOpts = {},
): Promise<T> {
  let res = await attempt(path, init);

  if (res.status === 401 && opts.auth) {
    const refreshed = await refresh();
    if (refreshed) res = await attempt(path, init);
  }

  if (!res.ok) {
    let problem: ProblemDetail = {
      title: res.statusText || "Request failed",
      status: res.status,
    };
    try {
      const ct = res.headers.get("content-type") || "";
      if (ct.includes("json")) problem = { ...problem, ...(await res.json()) };
    } catch {
      // body parse failure — keep status-derived defaults
    }
    throw new ApiError(problem);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
