/**
 * BFF route manifest — opaque ID → real Django path mapping.
 *
 * Each entry assigns a stable, opaque short ID to a (method, path-template)
 * tuple. The Next.js route handler at `app/api/bff/[id]/route.ts` reads this
 * manifest, validates the method, substitutes path params, and proxies to
 * Django. Result: the network tab shows `/api/bff/<id>` instead of
 * `/api/v1/marketplace/leads/`.
 *
 * Conventions:
 * - IDs are 8-12 characters, base36-style. Stable across deploys.
 * - Paths use `:slug` and `:id` placeholders that map to query/body params
 *   the client passes as `_path` (kept lightweight on purpose).
 * - Public endpoints don't need BFF treatment when they're SSR — server
 *   components hit Django directly and never appear in the network tab.
 *   We only obscure interactive client-driven mutations + rare client reads.
 *
 * Migration discipline: add a new entry here BEFORE you add the client call.
 * Never accept a request whose ID isn't in this manifest.
 */

export type BffMethod = "GET" | "POST" | "PATCH" | "PUT" | "DELETE";

export interface BffRoute {
  /** Opaque short id used in the URL */
  id: string;
  /** HTTP method client must use */
  method: BffMethod;
  /** Real Django path template; ":param" placeholders substituted from body._path */
  template: string;
  /** Should the client be authenticated? Defaults to true for mutations. */
  auth: boolean;
  /** Optional rate-limit hint applied at the BFF layer */
  rateLimit?: { window: number; max: number };
  /** Human note — for the manifest table; never sent to client */
  note: string;
}

export const BFF_ROUTES: BffRoute[] = [
  // ── Marketplace mutations ────────────────────────────────────────────
  {
    id: "lead-c0nnect",
    method: "POST",
    template: "/api/v1/leads/",
    auth: true,
    rateLimit: { window: 60, max: 10 },
    note: "Buyer submits a lead inquiry to a vendor",
  },
  {
    id: "lead-msg-snd",
    method: "POST",
    template: "/api/v1/leads/:lead_id/messages/",
    auth: true,
    rateLimit: { window: 60, max: 30 },
    note: "Send a lead conversation message",
  },
  {
    id: "lead-status",
    method: "PATCH",
    template: "/api/v1/leads/:lead_id/",
    auth: true,
    rateLimit: { window: 60, max: 20 },
    note: "Vendor updates lead status (contacted/won/lost)",
  },
  {
    id: "rev-write",
    method: "POST",
    template: "/api/v1/leads/:lead_id/review/",
    auth: true,
    rateLimit: { window: 60, max: 5 },
    note: "Buyer writes a review on a won lead",
  },

  // ── Forum interactions ───────────────────────────────────────────────
  {
    id: "forum-vote",
    method: "POST",
    template: "/api/v1/forum/votes/",
    auth: true,
    rateLimit: { window: 60, max: 30 },
    note: "Vote on a thread or reply",
  },
  {
    id: "forum-rply",
    method: "POST",
    template: "/api/v1/community/threads/:slug/replies/",
    auth: true,
    rateLimit: { window: 60, max: 15 },
    note: "Reply to a forum thread",
  },
  {
    id: "forum-thrd",
    method: "POST",
    template: "/api/v1/community/threads/",
    auth: true,
    rateLimit: { window: 60, max: 5 },
    note: "Create a new forum thread",
  },

  // ── Comments + flags ─────────────────────────────────────────────────
  {
    id: "cmt-write",
    method: "POST",
    template: "/api/v1/posts/:slug/comments/",
    auth: true,
    rateLimit: { window: 60, max: 15 },
    note: "Write a comment on a blog post",
  },
  {
    id: "cont-flag",
    method: "POST",
    template: "/api/v1/mod/flags/",
    auth: true,
    rateLimit: { window: 300, max: 20 },
    note: "Flag user-generated content",
  },

  // ── AI tools (mutations only — streams keep direct path) ─────────────
  {
    id: "tool-desc",
    method: "POST",
    template: "/api/v1/tools/description/",
    auth: true,
    rateLimit: { window: 60, max: 10 },
    note: "Description writer submission",
  },
  {
    id: "tool-furn",
    method: "POST",
    template: "/api/v1/tools/furniture-remover/",
    auth: true,
    rateLimit: { window: 60, max: 10 },
    note: "Furniture remover submission",
  },
  {
    id: "tool-cmpr",
    method: "POST",
    template: "/api/v1/tools/image-compressor/",
    auth: true,
    rateLimit: { window: 60, max: 60 },
    note: "Image compressor submission (high-rate, batch use)",
  },

  // ── Account + profile ────────────────────────────────────────────────
  {
    id: "me-update",
    method: "PATCH",
    template: "/api/v1/me/",
    auth: true,
    rateLimit: { window: 300, max: 20 },
    note: "Update own profile",
  },
  {
    id: "newsltr-sub",
    method: "POST",
    template: "/api/v1/me/newsletter/",
    auth: false,
    rateLimit: { window: 600, max: 5 },
    note: "Newsletter subscription (anon)",
  },
];

const ROUTE_BY_ID = new Map(BFF_ROUTES.map((r) => [r.id, r]));

export function lookupBffRoute(id: string): BffRoute | undefined {
  return ROUTE_BY_ID.get(id);
}

/**
 * Substitutes `:param` placeholders. We URL-encode every value AND reject any
 * value that, after encoding, contains characters that could break out of the
 * path segment ('/', '..', '?', '#', backslash). This prevents a client from
 * smuggling `_path: { lead_id: "../../admin" }` into the template and steering
 * the upstream fetch at an unintended Django route.
 */
export function buildTargetPath(
  template: string,
  pathParams: Record<string, string | number> = {},
): string {
  return template.replace(/:(\w+)/g, (_, key) => {
    const v = pathParams[key];
    if (v === undefined || v === null) {
      throw new Error(`Missing BFF path param: ${key}`);
    }
    const raw = String(v);
    // Block path-segment escapes outright. encodeURIComponent escapes '/' to
    // %2F but Caddy/Django may decode that back; strip first so there's no
    // ambiguity downstream.
    if (
      raw.includes("/") ||
      raw.includes("\\") ||
      raw.includes("..") ||
      raw.includes("?") ||
      raw.includes("#") ||
      /[\x00-\x1f]/.test(raw)
    ) {
      throw new Error(`Invalid BFF path param: ${key}`);
    }
    return encodeURIComponent(raw);
  });
}
