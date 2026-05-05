import Link from "next/link";
import type { Metadata } from "next";
import Container from "@/components/layout/Container";
import Hero from "@/components/marketing/Hero";
import SectionHeader from "@/components/marketing/SectionHeader";
import ScrollReveal from "@/components/reveal/ScrollReveal";
import PostCard from "@/components/content/PostCard";
import { safeServerFetch } from "@/lib/api/server";
import type { Pagination, Post, PostType } from "@/lib/api/types";
import { cn } from "@/lib/utils";
import NewsletterSubscribe from "./NewsletterSubscribe";

export const metadata: Metadata = {
  title: "Blog",
  description:
    "Yakima Web posts, plus blogs from verified local realtors. New writing every week.",
};

const FILTERS: Array<{ label: string; value: PostType | "all" }> = [
  { label: "All writing", value: "all" },
  { label: "Yakima Web", value: "org" },
  { label: "Realtor blogs", value: "blog" },
];

interface BlogPageProps {
  searchParams: Promise<{ type?: string; cursor?: string }>;
}

export default async function BlogIndexPage({ searchParams }: BlogPageProps) {
  const sp = await searchParams;
  const activeType = (sp.type as PostType | undefined) || undefined;

  const featuredQs = "?limit=3";
  const listQs = new URLSearchParams();
  listQs.set("limit", "12");
  if (activeType) listQs.set("type", activeType);
  if (sp.cursor) listQs.set("cursor", sp.cursor);

  const [featured, list] = await Promise.all([
    safeServerFetch<Pagination<Post>>(
      `/api/public/v1/posts/${featuredQs}`,
      {},
      { cache: "no-store" },
    ),
    safeServerFetch<Pagination<Post>>(
      `/api/public/v1/posts/?${listQs.toString()}`,
      {},
      { cache: "no-store" },
    ),
  ]);

  return (
    <>
      <Hero
        eyebrow="The blog"
        title="Stories, market truth, and the real Yakima Valley."
        subtitle="Yakima Web posts, plus blogs from verified local realtors. New writing every week."
        bgImage="/img/hero/hero-blog.jpg"
      />

      {featured && featured.results.length > 0 && (
        <section className="section-y">
          <Container>
            <ScrollReveal>
              <SectionHeader
                eyebrow="This week"
                title="Featured posts"
                description="Pulled from across Yakima Web and our verified realtor network."
              />
            </ScrollReveal>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-14">
              {featured.results.slice(0, 3).map((post, i) => (
                <ScrollReveal key={post.id} delay={0.1 + i * 0.08}>
                  <PostCard post={post} priority={i === 0} />
                </ScrollReveal>
              ))}
            </div>
          </Container>
        </section>
      )}

      <section className="section-y bg-deep border-y border-gold/14">
        <Container>
          <ScrollReveal>
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 mb-10">
              <SectionHeader
                eyebrow="Browse"
                title="All writing"
                className="!max-w-xl"
              />
              <nav
                aria-label="Filter posts by type"
                className="flex flex-wrap gap-2"
              >
                {FILTERS.map((f) => {
                  const isActive =
                    (!activeType && f.value === "all") || activeType === f.value;
                  const href =
                    f.value === "all" ? "/blog" : `/blog?type=${f.value}`;
                  return (
                    <Link
                      key={f.value}
                      href={href}
                      className={cn(
                        "px-5 py-2.5 text-[11px] uppercase tracking-luxe border transition-colors",
                        isActive
                          ? "bg-gold text-black border-gold"
                          : "border-gold/30 text-mist hover:border-gold/60 hover:text-gold",
                      )}
                    >
                      {f.label}
                    </Link>
                  );
                })}
              </nav>
            </div>
          </ScrollReveal>

          {list && list.results.length > 0 ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {list.results.map((post, i) => (
                  <ScrollReveal key={post.id} delay={0.05 + (i % 6) * 0.05}>
                    <PostCard post={post} />
                  </ScrollReveal>
                ))}
              </div>
              {list.next && (
                <div className="mt-12 text-center">
                  <Link
                    href={`/blog?${new URLSearchParams({
                      ...(activeType ? { type: activeType } : {}),
                      cursor: extractCursor(list.next),
                    }).toString()}`}
                    className="inline-flex items-center gap-2 uppercase tracking-cap text-xs px-8 py-4 border border-gold/52 text-gold hover:bg-gold hover:text-black transition-colors"
                  >
                    Load more
                  </Link>
                </div>
              )}
            </>
          ) : (
            <p className="text-mist text-sm">
              Nothing published in this view yet. Try another filter.
            </p>
          )}
        </Container>
      </section>

      <section className="section-y">
        <Container>
          <ScrollReveal>
            <NewsletterSubscribe />
          </ScrollReveal>
        </Container>
      </section>
    </>
  );
}

function extractCursor(nextUrl: string): string {
  try {
    const u = new URL(nextUrl, "http://x");
    return u.searchParams.get("cursor") || "";
  } catch {
    return "";
  }
}
