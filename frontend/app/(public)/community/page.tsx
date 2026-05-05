import Link from "next/link";
import type { Metadata } from "next";
import Container from "@/components/layout/Container";
import Hero from "@/components/marketing/Hero";
import SectionHeader from "@/components/marketing/SectionHeader";
import ScrollReveal from "@/components/reveal/ScrollReveal";
import ThreadCard from "@/components/forum/ThreadCard";
import { Card, CardBody } from "@/components/ui/Card";
import { safeServerFetch } from "@/lib/api/server";
import type { ForumThread, Pagination } from "@/lib/api/types";

export const metadata: Metadata = {
  title: "Community",
  description:
    "Real estate questions, market talk, local takes. AI-moderated. No franchise spam.",
};

interface FlairOption {
  slug: string;
  name: string;
  description: string;
  thread_count?: number;
}

const FLAIRS: FlairOption[] = [
  {
    slug: "question",
    name: "Question",
    description: "Open questions to anyone with local knowledge.",
  },
  {
    slug: "discussion",
    name: "Discussion",
    description: "Slow takes, sharp questions, neighborly debate.",
  },
  {
    slug: "help",
    name: "Help Needed",
    description: "Buyers, sellers, renters — ask the room.",
  },
  {
    slug: "local-news",
    name: "Local News",
    description: "What's actually happening in the Yakima Valley.",
  },
  {
    slug: "market",
    name: "Market Talk",
    description: "Central Washington data, trends, real numbers.",
  },
  {
    slug: "show-tell",
    name: "Show & Tell",
    description: "Renovations, listings, projects worth a look.",
  },
  {
    slug: "off-topic",
    name: "Off-Topic",
    description: "Local takes that don't fit anywhere else.",
  },
];

export default async function CommunityIndexPage() {
  const threads = await safeServerFetch<Pagination<ForumThread>>(
    "/api/public/v1/community/threads/?limit=15&sort=hot",
    {},
    { cache: "no-store" },
  );

  return (
    <>
      <Hero
        eyebrow="Community"
        title="Real estate questions, market talk, local takes."
        subtitle="A Reddit-shaped forum for Central Washington real estate. AI-moderated, license-tagged, run by people who actually live here."
        primary={{ label: "Browse threads", href: "/community/discussion" }}
        secondary={{ label: "Read the rules", href: "/guidelines" }}
        bgImage="/img/hero/hero-community.jpg"
      />

      <section className="section-y">
        <Container>
          <ScrollReveal>
            <SectionHeader
              eyebrow="Pick a corner"
              title="Browse by flair"
              description="Eight ways to slice the conversation."
            />
          </ScrollReveal>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-12">
            {FLAIRS.map((f, i) => (
              <ScrollReveal key={f.slug} delay={0.04 + (i % 8) * 0.04}>
                <Link
                  href={`/community/${f.slug}`}
                  className="block group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
                >
                  <Card className="h-full">
                    <CardBody>
                      <h3 className="font-serif text-xl text-ivory leading-tight group-hover:text-gold-hi transition-colors mb-2">
                        {f.name}
                      </h3>
                      <p className="text-mist text-sm leading-relaxed">
                        {f.description}
                      </p>
                    </CardBody>
                  </Card>
                </Link>
              </ScrollReveal>
            ))}
          </div>
        </Container>
      </section>

      <section className="section-y bg-deep border-y border-gold/14">
        <Container>
          <ScrollReveal>
            <div className="flex flex-col md:flex-row md:items-baseline md:justify-between gap-6 mb-10">
              <SectionHeader
                eyebrow="What's hot"
                title="Recent threads"
                className="!max-w-xl"
              />
              <Link
                href="/community/discussion"
                className="text-xs uppercase tracking-cap text-gold hover:text-gold-hi"
              >
                Open the forum
              </Link>
            </div>
          </ScrollReveal>

          {threads && threads.results.length > 0 ? (
            <div className="grid grid-cols-1 gap-4">
              {threads.results.slice(0, 15).map((t, i) => (
                <ScrollReveal key={t.id} delay={0.03 + (i % 10) * 0.03}>
                  <ThreadCard thread={t} />
                </ScrollReveal>
              ))}
            </div>
          ) : (
            <p className="text-mist text-sm">
              Threads will appear here once the community gets going.
            </p>
          )}
        </Container>
      </section>
    </>
  );
}
