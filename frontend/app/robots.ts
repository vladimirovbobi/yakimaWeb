import type { MetadataRoute } from "next";

const BASE = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

export default function robots(): MetadataRoute.Robots {
  const disallow = [
    "/api/",
    "/admin/",
    "/dashboard/",
    "/account/",
    "/realtor/",
    "/vendor/",
    "/mod/",
    "/ops/",
    "/operator/",
    "/notifications/",
    "/2fa/",
    "/login",
    "/signup",
    "/verify-email/",
    "/verify-email-sent",
    "/password-reset",
  ];
  return {
    rules: [
      { userAgent: "*", allow: "/", disallow },
      { userAgent: "GPTBot", allow: "/blog", disallow: ["/dashboard/", "/account/", "/admin/"] },
      { userAgent: "ClaudeBot", allow: "/blog", disallow: ["/dashboard/", "/account/", "/admin/"] },
    ],
    sitemap: `${BASE}/sitemap.xml`,
    host: BASE,
  };
}
