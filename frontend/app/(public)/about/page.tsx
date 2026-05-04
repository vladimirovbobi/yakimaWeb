import type { Metadata } from "next";
import Container from "@/components/layout/Container";
import Hero from "@/components/marketing/Hero";
import SectionHeader from "@/components/marketing/SectionHeader";
import ScrollReveal from "@/components/reveal/ScrollReveal";
import Link from "next/link";

export const metadata: Metadata = {
  title: "About",
  description:
    "Why Yakima Web exists, how we verify realtors, and how we keep the platform honest.",
};

const VALUES = [
  {
    eyebrow: "We're local",
    title: "Built for Central Washington, not built somewhere else.",
    body: "The major real estate sites are franchise machines. Yakima Web is for the Valley. Listings, vendors, threads, all centered on the people actually here.",
  },
  {
    eyebrow: "We verify",
    title: "Every realtor on this site has a real license.",
    body: "We check it through ARELLO, the cross-state license verification network. If your name is on a blog here, your license is current and on file.",
  },
  {
    eyebrow: "We moderate",
    title: "AI-moderated, human-overruled.",
    body: "Every comment, every reply, every listing passes a three-layer moderation pipeline before going live. Real humans review the edge cases. We don't ship spam.",
  },
];

export default function AboutPage() {
  return (
    <>
      <Hero
        eyebrow="About"
        title="A real-estate platform built for the place we live in."
        subtitle="Yakima Web is the connective tissue around the Central Washington real estate market. Verified realtors, vetted vendors, real conversation, and tools that pull their weight."
      />

      <section className="section-y">
        <Container>
          <div className="max-w-3xl">
            <div className="ey mb-5">The story</div>
            <h2 className="font-serif font-light text-ivory text-[clamp(2rem,4vw,2.75rem)] leading-[1.15]">
              Big real estate doesn't speak Yakima.
            </h2>
            <div className="prose-page mt-8">
              <p>
                The major listing sites optimize for ad clicks. The franchise
                blogs read like SEO sludge. None of it tells you what the Tieton
                drive-up actually feels like in March, or whether that house off
                Summitview backs onto the orchard or the highway.
              </p>
              <p>
                Yakima Web is the answer to that. Local realtors with verified
                licenses publish honest writing about the Valley. Local vendors
                publish their packages and get inquiries directly. Locals ask
                real questions in a Reddit-shaped forum that an AI moderator
                keeps tidy. Three audiences. One trustworthy hub.
              </p>
            </div>
          </div>
        </Container>
      </section>

      <section className="section-y bg-deep border-y border-gold/14">
        <Container>
          <ScrollReveal>
            <SectionHeader
              eyebrow="What we believe"
              title="Three principles. Then engineering."
            />
          </ScrollReveal>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-14">
            {VALUES.map((v, i) => (
              <ScrollReveal key={v.eyebrow} delay={0.08 + i * 0.06}>
                <div>
                  <div className="ey mb-4">{v.eyebrow}</div>
                  <h3 className="font-serif text-2xl text-ivory font-light leading-tight mb-4">
                    {v.title}
                  </h3>
                  <p className="text-mist text-sm leading-relaxed">{v.body}</p>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </Container>
      </section>

      <section id="marketplace" className="section-y">
        <Container>
          <div className="max-w-3xl">
            <div className="ey mb-5">How we verify</div>
            <h2 className="font-serif font-light text-ivory text-3xl">
              Every license, checked.
            </h2>
            <div className="prose-page mt-7">
              <p>
                When you sign up as a realtor, we run your license number
                through ARELLO - the system US state real-estate commissions use
                to share verification data. We store the raw response on file,
                check it again periodically, and surface a verified pip on your
                profile only when the license is current and active.
              </p>
              <p>
                If your license lapses, expires, or gets suspended, the pip
                comes off automatically. Yakima Web does not represent buyers
                or sellers. We're the platform. Your deal is yours.
              </p>
            </div>
          </div>
        </Container>
      </section>

      <section className="section-y bg-deep border-y border-gold/14">
        <Container>
          <div className="max-w-3xl">
            <div className="ey mb-5">Why we moderate</div>
            <h2 className="font-serif font-light text-ivory text-3xl">
              The forum is good because the moderation is.
            </h2>
            <div className="prose-page mt-7">
              <p>
                Every comment, post, and reply runs through a three-layer
                pipeline: structural checks, an AI classifier with adversarial
                fixtures hardened against prompt injection, and human review for
                the edge cases. Our pipeline never approves an attack.
              </p>
              <p>
                You can read the rules in full on the{" "}
                <Link href="/guidelines" className="text-gold underline">
                  guidelines page
                </Link>
                . The short version: stay on topic, no personal attacks, no
                spam, no fair-housing violations, no doxxing.
              </p>
            </div>
          </div>
        </Container>
      </section>
    </>
  );
}
