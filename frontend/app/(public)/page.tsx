import Link from "next/link";
import type { Metadata } from "next";
import Container from "@/components/layout/Container";
import Hero from "@/components/marketing/Hero";
import ScrollReveal from "@/components/reveal/ScrollReveal";
import CuratedFeed, {
  type FeedPost,
  type FeedThread,
  type FeedVoice,
} from "@/components/marketing/CuratedFeed";
import { safeServerFetch } from "@/lib/api/server";
import { breadcrumbLD, jsonLDScript } from "@/lib/seo";

interface ApiPost {
  id: number;
  slug: string;
  title: string;
  excerpt: string;
  body?: string;
  published_at: string;
  hero_image?: string | null;
  author_name?: string;
}

interface ApiThread {
  id: number;
  slug: string;
  title: string;
  body?: string;
  reply_count: number;
  vote_score?: number;
  score?: number;
  created_at: string;
  flair?: { label?: string; color?: string } | null;
  author_name?: string;
}

interface ApiRealtor {
  id: number;
  user?: { full_name?: string; slug?: string };
  full_name?: string;
  slug?: string;
  brokerage?: string;
  bio?: string;
  verification_status?: string;
}

interface Page<T> {
  results: T[];
}

export const metadata: Metadata = {
  title: "Where Yakima Valley talks about home",
  description:
    "Slow takes, sharp questions, and the people who actually know the Yakima Valley. A grounded local hub — verified, calm, built to make you smarter about home.",
  alternates: { canonical: "/" },
};

export const revalidate = 300;

function toFeedPost(p: ApiPost): FeedPost {
  return {
    id: p.id,
    slug: p.slug,
    title: p.title,
    excerpt: p.excerpt || (p.body || "").slice(0, 220),
    published_at: p.published_at,
    hero_image: p.hero_image ?? null,
    author_name: p.author_name,
  };
}

function toFeedThread(t: ApiThread): FeedThread {
  return {
    id: t.id,
    slug: t.slug,
    title: t.title,
    body: t.body,
    reply_count: t.reply_count,
    vote_score: t.vote_score ?? t.score ?? 0,
    created_at: t.created_at,
    flair: t.flair ?? null,
    author_name: t.author_name,
  };
}

function toFeedVoice(r: ApiRealtor): FeedVoice {
  return {
    id: r.id,
    slug: r.slug || r.user?.slug,
    name: r.full_name || r.user?.full_name || "Verified realtor",
    brokerage: r.brokerage,
    bio: r.bio,
    verified: (r.verification_status || "").toLowerCase() === "verified",
  };
}

export default async function HomePage() {
  const [postsResp, threadsResp, realtorsResp] = await Promise.all([
    safeServerFetch<Page<ApiPost>>(
      "/api/public/v1/posts/?limit=8",
      {},
      { next: { revalidate: 300 } },
    ),
    safeServerFetch<Page<ApiThread>>(
      "/api/public/v1/community/threads/?limit=6&sort=hot",
      {},
      { next: { revalidate: 300 } },
    ),
    safeServerFetch<Page<ApiRealtor>>(
      "/api/public/v1/realtors/?limit=3",
      {},
      { next: { revalidate: 600 } },
    ),
  ]);

  const allPosts = (postsResp?.results || []).map(toFeedPost);
  const featured = allPosts[0] || null;
  const posts = allPosts.slice(1);
  const threads = (threadsResp?.results || []).map(toFeedThread);
  const voices = (realtorsResp?.results || []).map(toFeedVoice);

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={jsonLDScript(
          breadcrumbLD([{ name: "Home", path: "/" }]),
        )}
      />

      <Hero
        eyebrow="Yakima Valley · Central Washington"
        title="Where Yakima talks about home."
        subtitle="Slow takes, sharp questions, and the people who actually know this valley. A grounded local hub — verified, calm, and built to make you smarter about home."
        primary={{ label: "Read this week's stories", href: "/blog" }}
        secondary={{ label: "Join the conversation", href: "/community" }}
      />

      <main id="main">
        <section className="section-y">
          <Container>
            <ScrollReveal>
              <div className="max-w-3xl">
                <p className="ey mb-4">This week in the valley</p>
                <h2 className="font-serif font-light text-ivory text-[clamp(1.75rem,3.5vw,2.5rem)] leading-[1.15]">
                  The conversations, the data, and the neighbors worth knowing.
                </h2>
                <p className="text-mist mt-5 leading-relaxed text-base md:text-lg">
                  Pull up a chair. Read a story, jump into a thread, get to know a verified realtor who actually lives down the street. No portals, no franchise spam — just the people and ideas that matter to home in Central Washington.
                </p>
              </div>
            </ScrollReveal>

            <div className="mt-14">
              <CuratedFeed
                featured={featured}
                posts={posts}
                threads={threads}
                voices={voices}
              />
            </div>
          </Container>
        </section>

        <section className="section-y bg-deep border-y border-gold/14">
          <Container>
            <ScrollReveal>
              <div className="grid lg:grid-cols-[1.1fr_auto] gap-10 lg:gap-16 items-center">
                <div>
                  <p className="ey mb-4">Are you a Washington-licensed realtor?</p>
                  <h2 className="font-serif font-light text-ivory text-[clamp(1.75rem,3.5vw,2.5rem)] leading-[1.1] max-w-2xl">
                    Bring your voice to the table.
                  </h2>
                  <p className="text-mist mt-5 leading-relaxed text-base md:text-lg max-w-2xl">
                    We verify every license through ARELLO before anything publishes. The badge means the words came from someone who actually holds the credential. Quiet platform. Local audience. No franchise pressure.
                  </p>
                </div>
                <div className="flex flex-col gap-3 lg:items-end">
                  <Link
                    href="/signup?role=realtor"
                    data-touch
                    className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-8 py-4 bg-gold text-black font-medium hover:bg-gold-hi transition-colors"
                  >
                    Verify your license
                  </Link>
                  <Link
                    href="/about"
                    className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-[11px] tracking-luxe text-mist hover:text-gold transition-colors"
                  >
                    What we stand for →
                  </Link>
                </div>
              </div>
            </ScrollReveal>
          </Container>
        </section>
      </main>
    </>
  );
}
