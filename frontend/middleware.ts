import { NextResponse, type NextRequest } from "next/server";

const PROTECTED_PREFIXES = [
  "/dashboard",
  "/account",
  "/realtor",
  "/operator",
  "/2fa",
];
const AUTH_PAGES = ["/login", "/signup"];

function isProtected(pathname: string) {
  return PROTECTED_PREFIXES.some((p) => pathname.startsWith(p));
}

function isAuthPage(pathname: string) {
  return AUTH_PAGES.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

function generateNonce() {
  const array = new Uint8Array(16);
  crypto.getRandomValues(array);
  return btoa(String.fromCharCode(...array));
}

export function middleware(req: NextRequest) {
  const { pathname, search } = req.nextUrl;

  const access = req.cookies.get("yw_access")?.value;
  const nonce = generateNonce();

  if (isProtected(pathname) && !access) {
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    url.search = `?next=${encodeURIComponent(pathname + search)}`;
    return NextResponse.redirect(url);
  }

  if (isAuthPage(pathname) && access) {
    const skip = req.nextUrl.searchParams.get("redirect") === "false";
    if (!skip) {
      const url = req.nextUrl.clone();
      url.pathname = "/dashboard";
      url.search = "";
      return NextResponse.redirect(url);
    }
  }

  const reqHeaders = new Headers(req.headers);
  reqHeaders.set("x-csp-nonce", nonce);

  const res = NextResponse.next({ request: { headers: reqHeaders } });
  res.headers.set("x-csp-nonce", nonce);
  return res;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml|.*\\..*).*)",
  ],
};
