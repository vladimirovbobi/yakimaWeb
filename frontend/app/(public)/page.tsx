import Link from "next/link";
import Container from "@/components/layout/Container";
import Hero from "@/components/marketing/Hero";
import SectionHeader from "@/components/marketing/SectionHeader";
import ScrollReveal from "@/components/reveal/ScrollReveal";
import { Card, CardBody } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import { safeServerFetch } from "@/lib/api/server";
import { formatDate } from "@/lib/utils";

interface Post {
  id: number;
  slug: string;
  title: string;
  excerpt: string;
  published_at: string;
  author_name?: string;
}

interface Service {
  id: number;
  slug: string;
  title: string;
  vendor_name: string;
  category: string;
  starting_price?: number | null;
}

interface Thread {
  id: number;
  slug: string;
  title: string;
  reply_count: number;
  vote_score: number;
  created_at: string;
}

interface Page<T> {
  results: T[];
}

const audiences = [
  {
    eyebrow: "For realtors",
    title: "Verified license. Captive audience.",
    body: "Get found by Yakima buyers. License-verified blogs, lead-magnet AI tools, and a market your competitors don't see.",
    href: "/realtors",
  },
  {
    eyebrow: "For vendors",
    title: "Lead-gen marketplace.",
    body: "Photographers, lenders, junk removal, 3D tours - publish packages, get qualified inquiries from local realtors.",
    href: "/vendors",
  },
  {
    eyebrow: "For buyers and sellers",
    title: "Community and market truth.",
    body: "Real threads, real comps, AI-moderated discussion. No franchise spam, no SEO sludge.",
    href: "/community",
  },
];

export default async function HomePage() {
  const [posts, services, threads] = await Promise.all([
    safeServerFetch<Page<Post>>(
      "/api/public/v1/posts/?limit=3&type=org",
      {},
      { cache: "no-store" },
    ),
    safeServerFetch<Page<Service>>(
      "/api/public/v1/services/?limit=3",
      {},
      { cache: "no-store" },
    ),
    safeServerFetch<Page<Thread>>(
      "/api/public/v1/community/threads/?limit=5",
      {},
      { cache: "no-store" },
    ),
  ]);

  return (
    <>
      <Hero
        eyebrow="Central Washington"
        title={`Central Washington's home for realtors, services, and market truth.`}
        subtitle="Verified realtor blogs. A vendor marketplace. AI tools to win listings. A real community. One platform, built for the Yakima Valley."
        primary={{ label: "Browse the marketplace", href: "/marketplace" }}
        secondary={{ label: "Sign up free", href: "/signup" }}
      />

      <section className="section-y">
        <Container>
          <ScrollReveal>
            <SectionHeader
              eyebrow="What is Yakima Web"
              title="Three audiences. One trustworthy hub."
              description="Most real estate sites are listing portals. We're the connective tissue around them - verified expertise, vendor lead-gen, and community truth."
            />
          </ScrollReveal>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-14">
            {audiences.map((a, i) => (
              <ScrollReveal key={a.eyebrow} delay={0.1 + i * 0.08}>
                <Card className="h-full">
                  <CardBody className="flex flex-col">
                    <div className="ey mb-4">{a.eyebrow}</div>
                    <h3 className="font-serif text-2xl text-ivory leading-tight font-light mb-4">
                      {a.title}
                    </h3>
                    <p className="text-mist leading-relaxed text-sm mb-8">
                      {a.body}
                    </p>
                    <Link
                      href={a.href}
                      className="mt-auto inline-flex items-center gap-3 text-xs uppercase tracking-cap text-gold pt-5 border-t border-gold/14 hover:tracking-luxe transition-[letter-spacing] duration-300"
                    >
                      Learn more
                      <svg
                        width="16"
                        height="10"
                        viewBox="0 0 16 10"
                        fill="none"
                        aria-hidden
                        className="transition-transform duration-300 group-hover:translate-x-1"
                      >
                        <path
                          d="M1 5h13m0 0L10 1m4 4l-4 4"
                          stroke="currentColor"
                          strokeWidth="1.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </Link>
                  </CardBody>
                </Card>
              </ScrollReveal>
            ))}
          </div>
        </Container>
      </section>

      <section className="section-y bg-deep border-y border-gold/14">
        <Container>
          <ScrollReveal>
            <div className="flex flex-col md:flex-row items-baseline justify-between gap-6 mb-12">
              <SectionHeader
                eyebrow="From the blog"
                title="Featured posts"
                className="!max-w-xl"
              />
              <Link
                href="/blog"
                className="text-xs uppercase tracking-cap text-gold hover:text-gold-hi"
              >
                Read all posts
              </Link>
            </div>
          </ScrollReveal>

          {posts && posts.results.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {posts.results.slice(0, 3).map((post, i) => (
                <ScrollReveal key={post.id} delay={0.1 + i * 0.08}>
                  <Link href={`/blog/${post.slug}`} className="block group">
                    <Card className="h-full">
                      <CardBody>
                        <p className="text-[11px] uppercase tracking-luxe text-mist mb-3">
                          {formatDate(post.published_at)}
                        </p>
                        <h3 className="font-serif text-xl text-ivory font-light leading-tight mb-3 group-hover:text-gold-hi transition-colors">
                          {post.title}
                        </h3>
                        <p className="text-mist text-sm leading-relaxed line-clamp-3">
                          {post.excerpt}
                        </p>
                      </CardBody>
                    </Card>
                  </Link>
                </ScrollReveal>
              ))}
            </div>
          ) : (
            <p className="text-mist text-sm">
              Posts will appear here once published.
            </p>
          )}
        </Container>
      </section>

      <section className="section-y">
        <Container>
          <ScrollReveal>
            <div className="flex flex-col md:flex-row items-baseline justify-between gap-6 mb-12">
              <SectionHeader
                eyebrow="Marketplace"
                title="Featured services"
                className="!max-w-xl"
              />
              <Link
                href="/marketplace"
                className="text-xs uppercase tracking-cap text-gold hover:text-gold-hi"
              >
                Browse all services
              </Link>
            </div>
          </ScrollReveal>

          {services && services.results.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {services.results.slice(0, 3).map((svc, i) => (
                <ScrollReveal key={svc.id} delay={0.1 + i * 0.08}>
                  <Link
                    href={`/marketplace/${svc.slug}`}
                    className="block group"
                  >
                    <Card className="h-full">
                      <CardBody>
                        <Badge tone="gold" className="mb-4">
                          {svc.category}
                        </Badge>
                        <h3 className="font-serif text-xl text-ivory font-light leading-tight mb-3 group-hover:text-gold-hi transition-colors">
                          {svc.title}
                        </h3>
                        <p className="text-mist text-sm">{svc.vendor_name}</p>
                        {svc.starting_price != null && (
                          <p className="font-serif text-gold text-2xl mt-5">
                            from ${svc.starting_price.toLocaleString()}
                          </p>
                        )}
                      </CardBody>
                    </Card>
                  </Link>
                </ScrollReveal>
              ))}
            </div>
          ) : (
            <p className="text-mist text-sm">
              Vendor listings will appear here once approved.
            </p>
          )}
        </Container>
      </section>

      <section className="section-y bg-deep border-y border-gold/14">
        <Container>
          <ScrollReveal>
            <div className="flex flex-col md:flex-row items-baseline justify-between gap-6 mb-12">
              <SectionHeader
                eyebrow="Community"
                title="Latest from the community"
                className="!max-w-xl"
              />
              <Link
                href="/community"
                className="text-xs uppercase tracking-cap text-gold hover:text-gold-hi"
              >
                Open the forum
              </Link>
            </div>
          </ScrollReveal>

          {threads && threads.results.length > 0 ? (
            <ul className="divide-y divide-gold/14 border-y border-gold/14">
              {threads.results.slice(0, 5).map((t, i) => (
                <ScrollReveal key={t.id} delay={0.05 + i * 0.05}>
                  <li>
                    <Link
                      href={`/community/${t.slug}`}
                      className="flex items-center justify-between gap-6 py-5 group"
                    >
                      <div className="min-w-0">
                        <h3 className="font-serif text-lg text-ivory leading-tight group-hover:text-gold-hi transition-colors">
                          {t.title}
                        </h3>
                        <p className="text-[11px] uppercase tracking-luxe text-mist mt-2">
                          {formatDate(t.created_at)}
                        </p>
                      </div>
                      <div className="flex gap-6 flex-shrink-0">
                        <span className="text-xs uppercase tracking-luxe text-mist">
                          <span className="text-ivory">{t.vote_score}</span>{" "}
                          votes
                        </span>
                        <span className="text-xs uppercase tracking-luxe text-mist">
                          <span className="text-ivory">{t.reply_count}</span>{" "}
                          replies
                        </span>
                      </div>
                    </Link>
                  </li>
                </ScrollReveal>
              ))}
            </ul>
          ) : (
            <p className="text-mist text-sm">
              Threads will appear here once the forum opens.
            </p>
          )}
        </Container>
      </section>

      <section className="section-y">
        <Container>
          <ScrollReveal>
            <div className="border border-gold/22 bg-deep p-10 md:p-16 text-center">
              <div className="ey mb-6">For realtors</div>
              <h2 className="font-serif font-light text-ivory text-[clamp(2rem,4vw,3rem)] leading-[1.1] max-w-2xl mx-auto">
                Verify your license. Publish to local buyers. Get found.
              </h2>
              <p className="text-mist mt-5 leading-relaxed max-w-xl mx-auto">
                ARELLO-verified profile. Local-only audience. AI tools you can't
                get on franchise sites.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center mt-10">
                <Link
                  href="/signup?role=realtor"
                  className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-8 py-4 bg-gold text-black font-medium hover:bg-gold-hi transition-colors"
                >
                  Verify your license
                </Link>
                <Link
                  href="/realtors"
                  className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-8 py-4 border border-gold/52 text-gold hover:bg-gold hover:text-black transition-colors"
                >
                  See what you get
                </Link>
              </div>
            </div>
          </ScrollReveal>
        </Container>
      </section>
    </>
  );
}
