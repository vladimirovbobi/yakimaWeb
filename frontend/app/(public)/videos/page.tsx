import type { Metadata } from "next";
import Container from "@/components/layout/Container";
import Hero from "@/components/marketing/Hero";
import ScrollReveal from "@/components/reveal/ScrollReveal";
import { safeServerFetch } from "@/lib/api/server";
import type { Pagination, SocialEmbed } from "@/lib/api/types";
import { formatDate } from "@/lib/utils";

export const metadata: Metadata = {
  title: "Video and social",
  description:
    "Yakima Web on YouTube and Instagram. Listing tours, neighborhood walks, market reads.",
};

export default async function VideosPage() {
  const social = await safeServerFetch<Pagination<SocialEmbed>>(
    "/api/public/v1/posts/social/?limit=24",
    {},
    { cache: "no-store" },
  );

  const items = social?.results || [];

  return (
    <>
      <Hero
        eyebrow="Video and social"
        title="Yakima Web in motion."
        subtitle="Listing walk-throughs, neighborhood tours, and market reads. Pulled live from our YouTube and Instagram."
      />

      <section className="section-y">
        <Container>
          {items.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {items.map((item, i) => (
                <ScrollReveal key={item.id} delay={0.04 + (i % 6) * 0.04}>
                  <article className="bg-deep border border-gold/14 hover:border-gold/35 transition-colors overflow-hidden">
                    <div className="relative aspect-video bg-warm">
                      <iframe
                        src={item.embed_url}
                        title={item.title}
                        loading="lazy"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                        allowFullScreen
                        className="absolute inset-0 w-full h-full"
                      />
                    </div>
                    <div className="p-5">
                      <div className="flex items-center justify-between gap-3 mb-2">
                        <span className="text-[10px] uppercase tracking-luxe text-gold">
                          {item.platform === "youtube"
                            ? "YouTube"
                            : "Instagram"}
                        </span>
                        <span className="text-[11px] uppercase tracking-luxe text-dim">
                          {formatDate(item.posted_at)}
                        </span>
                      </div>
                      <h3 className="font-serif text-lg text-ivory leading-tight">
                        {item.title}
                      </h3>
                    </div>
                  </article>
                </ScrollReveal>
              ))}
            </div>
          ) : (
            <p className="text-mist text-sm">
              Videos will appear here once we publish.
            </p>
          )}
        </Container>
      </section>
    </>
  );
}
