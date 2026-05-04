import Link from "next/link";
import type { Metadata } from "next";
import Container from "@/components/layout/Container";
import Hero from "@/components/marketing/Hero";
import SectionHeader from "@/components/marketing/SectionHeader";
import ScrollReveal from "@/components/reveal/ScrollReveal";
import { Card, CardBody } from "@/components/ui/Card";

export const metadata: Metadata = {
  title: "AI tools",
  description:
    "Tools built for the realtor's day. Furniture remover and listing description writer, both AI-moderated, both Yakima-aware.",
};

const TOOLS = [
  {
    eyebrow: "Listing prep",
    name: "Furniture remover",
    summary: "Empty a furnished room in 30 seconds. Upload a photo, get a clean shell.",
    detail:
      "Drop a photo of any room. The model strips furniture, decor, and clutter while keeping the architecture - flooring, walls, light - intact. Ideal for vacant tours, virtual staging prep, or rebranding a tired listing.",
    cta: "Try furniture remover",
    href: "/dashboard/tools/furniture-remover",
  },
  {
    eyebrow: "Listing copy",
    name: "Description writer",
    summary:
      "Listing copy in your voice, with Fair Housing already checked.",
    detail:
      "Paste your listing details (beds, baths, neighborhood, the things that actually matter). Get a clean, MLS-ready description in three voices: factual, warm, or punchy. Fair Housing scrubbed before you ever see the draft.",
    cta: "Try description writer",
    href: "/dashboard/tools/description-writer",
  },
];

const STEPS = [
  {
    n: "01",
    title: "Sign in",
    body: "Free account. Realtors get extended quotas after license verify.",
  },
  {
    n: "02",
    title: "Drop your input",
    body: "Photo, listing details, or a paste of your draft. Whatever the tool needs.",
  },
  {
    n: "03",
    title: "Get clean output",
    body: "Moderated, watermarked where appropriate, ready to send to clients.",
  },
];

export default function ToolsLandingPage() {
  return (
    <>
      <Hero
        eyebrow="AI tools"
        title="Tools built for the realtor's day."
        subtitle="Two tools, both narrow, both useful. Run them on your own listings. Output is yours."
        primary={{ label: "See how it works", href: "#how" }}
      />

      <section className="section-y">
        <Container>
          <ScrollReveal>
            <SectionHeader
              eyebrow="What's available"
              title="Two tools. Both made to actually save time."
            />
          </ScrollReveal>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-14">
            {TOOLS.map((t, i) => (
              <ScrollReveal key={t.name} delay={0.1 + i * 0.1}>
                <Card className="h-full">
                  <CardBody className="flex flex-col">
                    <div className="ey mb-4">{t.eyebrow}</div>
                    <h3 className="font-serif text-3xl text-ivory leading-tight font-light mb-4">
                      {t.name}
                    </h3>
                    <p className="text-gold text-sm leading-relaxed mb-5">
                      {t.summary}
                    </p>
                    <p className="text-mist text-sm leading-relaxed mb-8">
                      {t.detail}
                    </p>
                    <Link
                      href={t.href}
                      className="mt-auto inline-flex items-center gap-3 text-xs uppercase tracking-cap text-gold pt-5 border-t border-gold/14 hover:tracking-luxe transition-[letter-spacing] duration-300"
                    >
                      {t.cta}
                      <svg
                        width="16"
                        height="10"
                        viewBox="0 0 16 10"
                        fill="none"
                        aria-hidden
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

      <section id="how" className="section-y bg-deep border-y border-gold/14">
        <Container>
          <ScrollReveal>
            <SectionHeader
              eyebrow="How it works"
              title="Three steps."
              align="center"
              className="mx-auto"
            />
          </ScrollReveal>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-14">
            {STEPS.map((s, i) => (
              <ScrollReveal key={s.n} delay={0.1 + i * 0.08}>
                <div className="text-center">
                  <div className="font-serif text-gold text-5xl mb-3">{s.n}</div>
                  <h3 className="font-serif text-2xl text-ivory mb-3">
                    {s.title}
                  </h3>
                  <p className="text-mist text-sm leading-relaxed max-w-xs mx-auto">
                    {s.body}
                  </p>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </Container>
      </section>

      <section className="section-y">
        <Container>
          <ScrollReveal>
            <div className="border border-gold/22 bg-deep p-10 md:p-14">
              <div className="ey mb-3">Limits</div>
              <h2 className="font-serif font-light text-ivory text-3xl mb-5">
                Free, with rate limits.
              </h2>
              <p className="text-mist leading-relaxed max-w-2xl mb-3">
                10 runs per hour for any signed-in user. Verified realtors get a
                higher quota and priority queue. We rate-limit to keep costs
                sane and to stop scrapers - it's not artificial scarcity.
              </p>
              <p className="text-mist leading-relaxed max-w-2xl">
                Every output passes our moderation pipeline before it lands in
                your hands. Logs are kept for audit per ARELLO and Fair Housing
                requirements.
              </p>
            </div>
          </ScrollReveal>
        </Container>
      </section>
    </>
  );
}
