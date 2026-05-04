import "server-only";
import { cookies } from "next/headers";
import { ApiError, type ProblemDetail } from "./fetch";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface ServerFetchOpts {
  auth?: boolean;
  cache?: RequestCache;
  next?: NextFetchRequestConfig;
}

export async function serverFetch<T>(
  path: string,
  init: RequestInit = {},
  opts: ServerFetchOpts = {},
): Promise<T> {
  const url = path.startsWith("http") ? path : `${BASE}${path}`;
  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");

  const headers = new Headers(init.headers);
  if (!headers.has("Accept")) headers.set("Accept", "application/json");
  headers.set("X-Requested-With", "XMLHttpRequest");
  if (cookieHeader) headers.set("cookie", cookieHeader);
  if (init.body && !headers.has("Content-Type"))
    headers.set("Content-Type", "application/json");

  const res = await fetch(url, {
    ...init,
    headers,
    cache: opts.cache ?? "no-store",
    next: opts.next,
  });

  if (!res.ok) {
    let problem: ProblemDetail = {
      title: res.statusText || "Request failed",
      status: res.status,
    };
    try {
      const ct = res.headers.get("content-type") || "";
      if (ct.includes("json")) problem = { ...problem, ...(await res.json()) };
    } catch {
      // body parse failure
    }
    throw new ApiError(problem);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export async function safeServerFetch<T>(
  path: string,
  init: RequestInit = {},
  opts: ServerFetchOpts = {},
): Promise<T | null> {
  try {
    return await serverFetch<T>(path, init, opts);
  } catch {
    return null;
  }
}
