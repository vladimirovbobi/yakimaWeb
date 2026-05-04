import type { MetadataRoute } from "next";
import { safeServerFetch } from "@/lib/api/server";

const BASE = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

interface IndexedPost {
  slug: string;
  updated_at?: string;
  published_at?: string;
}
interface IndexedThread {
  slug: string;
  created_at: string;
}
interface IndexedVendor {
  slug: string;
  updated_at?: string;
}
interface IndexedService {
  slug: string;
  updated_at?: string;
}
interface Page<T> {
  results: T[];
}

const STATIC_ROUTES: Array<{ path: string; priority: number; changeFreq: MetadataRoute.Sitemap[number]["changeFrequency"] }> = [
  { path: "/", priority: 1.0, changeFreq: "daily" },
  { path: "/about", priority: 0.6, changeFreq: "monthly" },
  { path: "/blog", priority: 0.9, changeFreq: "daily" },
  { path: "/community", priority: 0.9, changeFreq: "hourly" },
  { path: "/services", priority: 0.85, changeFreq: "daily" },
  { path: "/tools", priority: 0.7, changeFreq: "weekly" },
  { path: "/videos", priority: 0.5, changeFreq: "weekly" },
  { path: "/guidelines", priority: 0.4, changeFreq: "monthly" },
  { path: "/privacy", priority: 0.3, changeFreq: "yearly" },
  { path: "/terms", priority: 0.3, changeFreq: "yearly" },
];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();

  const [posts, threads, vendors, services] = await Promise.all([
    safeServerFetch<Page<IndexedPost>>("/api/public/v1/posts/?limit=500", {}, { next: { revalidate: 600 } }),
    safeServerFetch<Page<IndexedThread>>("/api/public/v1/community/threads/?limit=500", {}, { next: { revalidate: 600 } }),
    safeServerFetch<Page<IndexedVendor>>("/api/public/v1/vendors/?limit=500", {}, { next: { revalidate: 600 } }),
    safeServerFetch<Page<IndexedService>>("/api/public/v1/services/?limit=500", {}, { next: { revalidate: 600 } }),
  ]);

  const staticEntries: MetadataRoute.Sitemap = STATIC_ROUTES.map((r) => ({
    url: `${BASE}${r.path}`,
    lastModified: now,
    changeFrequency: r.changeFreq,
    priority: r.priority,
  }));

  const postEntries: MetadataRoute.Sitemap = (posts?.results || []).map((p) => ({
    url: `${BASE}/blog/${p.slug}`,
    lastModified: p.updated_at || p.published_at ? new Date(p.updated_at || p.published_at!) : now,
    changeFrequency: "weekly",
    priority: 0.7,
  }));

  const threadEntries: MetadataRoute.Sitemap = (threads?.results || []).map((t) => ({
    url: `${BASE}/community/${t.slug}`,
    lastModified: new Date(t.created_at),
    changeFrequency: "weekly",
    priority: 0.6,
  }));

  const vendorEntries: MetadataRoute.Sitemap = (vendors?.results || []).map((v) => ({
    url: `${BASE}/services/vendors/${v.slug}`,
    lastModified: v.updated_at ? new Date(v.updated_at) : now,
    changeFrequency: "weekly",
    priority: 0.65,
  }));

  const serviceEntries: MetadataRoute.Sitemap = (services?.results || []).map((s) => ({
    url: `${BASE}/services/${s.slug}`,
    lastModified: s.updated_at ? new Date(s.updated_at) : now,
    changeFrequency: "weekly",
    priority: 0.6,
  }));

  return [...staticEntries, ...postEntries, ...threadEntries, ...vendorEntries, ...serviceEntries];
}
