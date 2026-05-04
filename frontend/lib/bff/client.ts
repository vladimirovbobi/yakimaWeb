/**
 * BFF client helper — call by manifest ID, path/query params, and body.
 *
 * Use this for client-component mutations + interactive reads where you want
 * the network tab to show `/api/bff/<id>` rather than `/api/v1/...`.
 *
 * Server components should keep using `safeServerFetch` — they hit Django
 * directly server-side and never appear in the browser network tab anyway.
 *
 * Example:
 *
 *   await bffCall("forum-vote", {
 *     body: { target_type: "thread", target_id: 12, value: 1 },
 *   });
 *
 *   await bffCall("lead-msg-snd", {
 *     pathParams: { lead_id: 42 },
 *     body: { body: "Sounds good — Tuesday at 10?" },
 *   });
 */
import { ApiError, type ProblemDetail } from "@/lib/api/fetch";
import { lookupBffRoute, type BffMethod } from "./routes";

interface BffCallOptions {
  pathParams?: Record<string, string | number>;
  query?: Record<string, string | number | boolean>;
  body?: unknown;
  method?: BffMethod;
  csrfToken?: string;
}

export async function bffCall<T>(id: string, opts: BffCallOptions = {}): Promise<T> {
  const route = lookupBffRoute(id);
  if (!route) {
    throw new Error(`Unknown BFF route id: ${id}`);
  }
  const method = opts.method ?? route.method;

  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (opts.csrfToken) headers["X-CSRFToken"] = opts.csrfToken;

  const init: RequestInit = {
    method,
    headers,
    credentials: "include",
  };

  if (method !== "GET" && method !== "DELETE") {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify({
      ...(typeof opts.body === "object" && opts.body !== null ? opts.body : {}),
      ...(opts.pathParams ? { _path: opts.pathParams } : {}),
      ...(opts.query ? { _query: opts.query } : {}),
    });
  }

  // GET/DELETE carry _path + _query as JSON-encoded URL params if needed.
  let url = `/api/bff/${id}`;
  if (method === "GET" || method === "DELETE") {
    const usp = new URLSearchParams();
    if (opts.pathParams) {
      for (const [k, v] of Object.entries(opts.pathParams)) {
        usp.set(`_p_${k}`, String(v));
      }
    }
    if (opts.query) {
      for (const [k, v] of Object.entries(opts.query)) {
        if (v == null || v === "") continue;
        usp.set(k, String(v));
      }
    }
    const s = usp.toString();
    if (s) url += `?${s}`;
  }

  const res = await fetch(url, init);
  if (!res.ok) {
    let detail: ProblemDetail = {
      title: res.statusText || "Request failed",
      status: res.status,
    };
    try {
      const ct = res.headers.get("content-type") || "";
      if (ct.includes("json")) {
        detail = { ...detail, ...(await res.json()) };
      }
    } catch {
      // ignore body parse failure
    }
    throw new ApiError(detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
