import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Container from "@/components/layout/Container";
import ScrollReveal from "@/components/reveal/ScrollReveal";
import ThreadCard from "@/components/forum/ThreadCard";
import { safeServerFetch } from "@/lib/api/server";
import { getCurrentUser } from "@/lib/auth/server";
import type { ForumThread, Pagination } from "@/lib/api/types";
import { cn } from "@/lib/utils";

const FLAIR_INFO: Record<string, { name: string; description: string }> = {
  buying: {
    name: "Buying",
    description: "First-time buyers, comps, what to look out for.",
  },
  selling: {
    name: "Selling",
    description: "Pricing, prep, when to sit and when to move.",
  },
  market: {
    name: "Market",
    description: "Yakima Valley data, trends, real numbers.",
  },
  renting: {
    name: "Renting",
    description: "Tenants, landlords, leases, the gray areas.",
  },
  ask: {
    name: "Ask Yakima",
    description: "Open questions to anyone with local knowledge.",
  },
  vendors: {
    name: "Vendors",
    description: "Recommendations, reviews, who's actually any good.",
  },
  neighborhood: {
    name: "Neighborhoods",
    description: "Selah vs Terrace Heights, schools, commute, vibe.",
  },
  general: {
    name: "General",
    description: "Local takes that don't fit anywhere else.",
  },
};

const SORTS = [
  { key: "hot", label: "Hot" },
  { key: "new", label: "New" },
  { key: "top", label: "Top" },
] as const;

type Sort = (typeof SORTS)[number]["key"];

interface FlairPageProps {
  params: Promise<{ flair: string }>;
  searchParams: Promise<{ sort?: string; cursor?: string }>;
}

export async function generateMetadata({
  params,
}: FlairPageProps): Promise<Metadata> {
  const { flair } = await params;
  const info = FLAIR_INFO[flair];
  if (!info) return { title: "Flair" };
  return {
    title: `${info.name} threads`,
    description: info.description,
  };
}

export default async function FlairPage({
  params,
  searchParams,
}: FlairPageProps) {
  const { flair } = await params;
  const sp = await searchParams;
  const info = FLAIR_INFO[flair];
  if (!info) notFound();

  const sort: Sort = (sp.sort as Sort) || "hot";

  const qs = new URLSearchParams();
  qs.set("flair", flair);
  qs.set("sort", sort);
  qs.set("limit", "20");
  if (sp.cursor) qs.set("cursor", sp.cursor);

  const [threads, user] = await Promise.all([
    safeServerFetch<Pagination<ForumThread>>(
      `/api/public/v1/community/threads/?${qs.toString()}`,
      {},
      { cache: "no-store" },
    ),
    getCurrentUser(),
  ]);

  const startHref = user
    ? `/dashboard?compose=thread&flair=${flair}`
    : `/login?next=${encodeURIComponent(`/community/${flair}`)}`;

  return (
    <section className="section-y">
      <Container>
        <Link
          href="/community"
          className="inline-flex items-center gap-2 text-[11px] uppercase tracking-luxe text-mist hover:text-gold mb-8"
        >
          <svg
            width="12"
            height="10"
            viewBox="0 0 12 10"
            fill="none"
            aria-hidden
          >
            <path
              d="M11 5H1m0 0l4-4M1 5l4 4"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          All flairs
        </Link>

        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6 mb-10">
          <div>
            <div className="ey mb-3">{info.name}</div>
            <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4vw,3rem)] leading-[1.1]">
              {info.description}
            </h1>
          </div>
          <Link
            href={startHref}
            className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-6 py-3 bg-gold text-black font-medium hover:bg-gold-hi transition-colors flex-shrink-0"
          >
            Start a thread
          </Link>
        </div>

        <div
          role="tablist"
          aria-label="Sort threads"
          className="flex gap-1 border-b border-gold/14 mb-8"
        >
          {SORTS.map((s) => {
            const isActive = sort === s.key;
            return (
              <Link
                key={s.key}
                href={`/community/${flair}?sort=${s.key}`}
                role="tab"
                aria-selected={isActive}
                className={cn(
                  "px-5 py-3 text-[11px] uppercase tracking-luxe transition-colors -mb-px border-b-2",
                  isActive
                    ? "text-gold border-gold"
                    : "text-mist border-transparent hover:text-ivory",
                )}
              >
                {s.label}
              </Link>
            );
          })}
        </div>

        {threads && threads.results.length > 0 ? (
          <>
            <div className="grid grid-cols-1 gap-4">
              {threads.results.map((t, i) => (
                <ScrollReveal key={t.id} delay={0.03 + (i % 10) * 0.03}>
                  <ThreadCard thread={t} showFlair={false} />
                </ScrollReveal>
              ))}
            </div>
            {threads.next && (
              <div className="mt-12 text-center">
                <Link
                  href={appendCursor(threads.next, flair, sort)}
                  className="inline-flex items-center gap-2 uppercase tracking-cap text-xs px-8 py-4 border border-gold/52 text-gold hover:bg-gold hover:text-black transition-colors"
                >
                  Load more
                </Link>
              </div>
            )}
          </>
        ) : (
          <p className="text-mist text-sm">
            No threads in {info.name} yet. Start one.
          </p>
        )}
      </Container>
    </section>
  );
}

function appendCursor(nextUrl: string, flair: string, sort: string): string {
  try {
    const u = new URL(nextUrl, "http://x");
    const cursor = u.searchParams.get("cursor");
    const out = new URLSearchParams({ sort });
    if (cursor) out.set("cursor", cursor);
    return `/community/${flair}?${out.toString()}`;
  } catch {
    return `/community/${flair}`;
  }
}
