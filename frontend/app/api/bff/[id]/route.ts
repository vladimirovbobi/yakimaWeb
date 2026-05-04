import { NextResponse, type NextRequest } from "next/server";
import { cookies } from "next/headers";
import { buildTargetPath, lookupBffRoute, type BffMethod } from "@/lib/bff/routes";

/**
 * BFF / Network-Tab Obscuration Proxy.
 *
 * Maps `/api/bff/<opaque-id>` → real Django endpoint server-side. The
 * browser network tab never sees `/api/v1/...` URLs from client-driven
 * mutations or interactive reads.
 *
 * Security:
 * - Same-origin only (Origin header check). Cross-origin = 403.
 * - Method must match the manifest entry exactly. Wrong method = 405.
 * - Auth-required routes: must carry `yw_access` cookie. Missing = 401.
 * - The opaque ID is the only public surface; the real Django path is
 *   never echoed in error responses.
 */

const DJANGO_BASE =
  process.env.INTERNAL_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://api:8000";

function corsBlock(): NextResponse {
  return NextResponse.json(
    { type: "about:blank", title: "forbidden", status: 403 },
    { status: 403 },
  );
}

function methodMismatch(): NextResponse {
  return NextResponse.json(
    { type: "about:blank", title: "method_not_allowed", status: 405 },
    { status: 405 },
  );
}

function unknownRoute(): NextResponse {
  return NextResponse.json(
    { type: "about:blank", title: "not_found", status: 404 },
    { status: 404 },
  );
}

function authRequired(): NextResponse {
  return NextResponse.json(
    { type: "about:blank", title: "auth_required", status: 401 },
    { status: 401 },
  );
}

interface BffRequestBody {
  /** Path params for `:slug`/`:id` substitution */
  _path?: Record<string, string | number>;
  /** Optional query string params */
  _query?: Record<string, string | number | boolean>;
  /** Forwarded body — anything not under _path/_query */
  [k: string]: unknown;
}

async function isSameOrigin(req: NextRequest): Promise<boolean> {
  const origin = req.headers.get("origin");
  const host   = req.headers.get("host");
  if (!origin || !host) {
    // Server-side fetches won't have Origin; same-origin by default for those.
    return true;
  }
  try {
    const url = new URL(origin);
    return url.host === host;
  } catch {
    return false;
  }
}

async function handle(
  req: NextRequest,
  expected: BffMethod,
  ctx: { params: Promise<{ id: string }> },
): Promise<NextResponse> {
  if (!(await isSameOrigin(req))) return corsBlock();

  const { id } = await ctx.params;
  const route = lookupBffRoute(id);
  if (!route) return unknownRoute();
  if (route.method !== expected) return methodMismatch();

  if (route.auth) {
    const cookieStore = await cookies();
    if (!cookieStore.get("yw_access")?.value) return authRequired();
  }

  // Pull _path + _query out of the body without leaking them to Django.
  let body: BffRequestBody = {};
  let bodyText: string | null = null;
  if (expected !== "GET" && expected !== "DELETE") {
    try {
      const ct = req.headers.get("content-type") || "";
      if (ct.includes("application/json")) {
        body = (await req.json()) as BffRequestBody;
      } else {
        bodyText = await req.text();
      }
    } catch {
      // empty body is fine
    }
  }
  const { _path = {}, _query = {}, ...forwardBody } = body;

  let target: string;
  try {
    target = buildTargetPath(route.template, _path);
  } catch {
    return NextResponse.json(
      { type: "about:blank", title: "missing_path_param", status: 400 },
      { status: 400 },
    );
  }

  const qsEntries = Object.entries(_query).filter(
    ([, v]) => v !== undefined && v !== null && v !== "",
  );
  const qs = qsEntries.length
    ? "?" + qsEntries.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`).join("&")
    : "";

  const upstreamUrl = `${DJANGO_BASE}${target}${qs}`;

  // Forward cookies, CSRF token, and a trimmed set of safe headers.
  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join("; ");
  const fwdHeaders = new Headers();
  fwdHeaders.set("X-Requested-With", "XMLHttpRequest");
  fwdHeaders.set("X-Forwarded-Proto", req.nextUrl.protocol.replace(":", ""));
  fwdHeaders.set("X-Forwarded-Host", req.headers.get("host") || "");
  fwdHeaders.set("X-Forwarded-For", req.headers.get("x-forwarded-for") || req.headers.get("x-real-ip") || "");
  fwdHeaders.set("Accept", "application/json");
  if (cookieHeader) fwdHeaders.set("Cookie", cookieHeader);
  const csrf = req.headers.get("x-csrftoken");
  if (csrf) fwdHeaders.set("X-CSRFToken", csrf);

  let upstreamBody: BodyInit | undefined = undefined;
  if (expected !== "GET" && expected !== "DELETE") {
    if (bodyText !== null) {
      upstreamBody = bodyText;
      const ct = req.headers.get("content-type");
      if (ct) fwdHeaders.set("Content-Type", ct);
    } else if (Object.keys(forwardBody).length > 0) {
      fwdHeaders.set("Content-Type", "application/json");
      upstreamBody = JSON.stringify(forwardBody);
    }
  }

  const upstream = await fetch(upstreamUrl, {
    method: expected,
    headers: fwdHeaders,
    body: upstreamBody,
    redirect: "manual",
    cache: "no-store",
  });

  // Stream the response body back. We deliberately don't echo the upstream
  // path or any internal headers.
  const respHeaders = new Headers();
  const passThrough = ["content-type", "content-length", "cache-control"];
  for (const h of passThrough) {
    const v = upstream.headers.get(h);
    if (v) respHeaders.set(h, v);
  }
  const respBody = await upstream.arrayBuffer();
  return new NextResponse(respBody, {
    status: upstream.status,
    headers: respHeaders,
  });
}

export async function GET(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  return handle(req, "GET", ctx);
}
export async function POST(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  return handle(req, "POST", ctx);
}
export async function PATCH(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  return handle(req, "PATCH", ctx);
}
export async function PUT(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  return handle(req, "PUT", ctx);
}
export async function DELETE(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  return handle(req, "DELETE", ctx);
}
