import Link from "next/link";
import type { Metadata } from "next";
import Container from "@/components/layout/Container";
import Hero from "@/components/marketing/Hero";
import SectionHeader from "@/components/marketing/SectionHeader";
import ScrollReveal from "@/components/reveal/ScrollReveal";
import ServiceCard from "@/components/marketplace/ServiceCard";
import VendorChip from "@/components/marketplace/VendorChip";
import { Card, CardBody } from "@/components/ui/Card";
import { safeServerFetch } from "@/lib/api/server";
import type {
  Category,
  Pagination,
  Service,
  VendorProfile,
} from "@/lib/api/types";
import ServicesFilters from "./ServicesFilters";

export const metadata: Metadata = {
  title: "Marketplace",
  description:
    "Local services. Real reviews. No middleman fees. Photographers, lenders, junk removal, 3D tours, and more.",
};

interface ServicesIndexProps {
  searchParams: Promise<{
    category?: string;
    q?: string;
    min_price?: string;
    max_price?: string;
    has_bundle?: string;
    cursor?: string;
  }>;
}

export default async function ServicesIndexPage({
  searchParams,
}: ServicesIndexProps) {
  const sp = await searchParams;

  const listQs = new URLSearchParams();
  listQs.set("limit", "12");
  if (sp.category) listQs.set("category", sp.category);
  if (sp.q) listQs.set("q", sp.q);
  if (sp.min_price) listQs.set("min_price", sp.min_price);
  if (sp.max_price) listQs.set("max_price", sp.max_price);
  if (sp.has_bundle === "1") listQs.set("has_bundle", "1");
  if (sp.cursor) listQs.set("cursor", sp.cursor);

  const [categories, services, featuredVendors] = await Promise.all([
    safeServerFetch<Category[]>(
      "/api/public/v1/services/categories/",
      {},
      { cache: "no-store" },
    ),
    safeServerFetch<Pagination<Service>>(
      `/api/public/v1/services/?${listQs.toString()}`,
      {},
      { cache: "no-store" },
    ),
    safeServerFetch<Pagination<VendorProfile>>(
      "/api/public/v1/services/vendors/?featured=1&limit=5",
      {},
      { cache: "no-store" },
    ),
  ]);

  const topLevel = (categories || []).filter((c) => !c.parent_id);

  return (
    <>
      <Hero
        eyebrow="Marketplace"
        title="Local services. Real reviews. No middleman fees."
        subtitle="Photographers, lenders, junk removal, 3D tours - publish your packages or hire someone close to home. Lead-gen only. We don't take a cut."
        primary={{ label: "List your service", href: "/dashboard/vendor/onboard" }}
        secondary={{ label: "How it works", href: "/about#marketplace" }}
      />

      <section className="section-y">
        <Container>
          <ScrollReveal>
            <SectionHeader
              eyebrow="Browse by trade"
              title="What do you need done?"
              description="Eight trades for the way real estate actually works in Yakima."
            />
          </ScrollReveal>

          {topLevel.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mt-12">
              {topLevel.map((c, i) => (
                <ScrollReveal key={c.id} delay={0.05 + (i % 8) * 0.04}>
                  <Link
                    href={`/services?category=${c.slug}`}
                    className="block group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
                  >
                    <Card className="h-full">
                      <CardBody>
                        <h3 className="font-serif text-lg text-ivory leading-tight group-hover:text-gold-hi transition-colors">
                          {c.name}
                        </h3>
                        {c.service_count != null && (
                          <p className="text-[11px] uppercase tracking-luxe text-mist mt-3">
                            {c.service_count} listed
                          </p>
                        )}
                      </CardBody>
                    </Card>
                  </Link>
                </ScrollReveal>
              ))}
            </div>
          ) : (
            <p className="text-mist text-sm mt-8">
              Categories will appear here once vendors onboard.
            </p>
          )}
        </Container>
      </section>

      <section className="section-y bg-deep border-y border-gold/14">
        <Container>
          <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-10">
            <aside className="lg:sticky lg:top-28 lg:self-start">
              <ServicesFilters
                categories={categories || []}
                active={{
                  category: sp.category,
                  q: sp.q,
                  min_price: sp.min_price,
                  max_price: sp.max_price,
                  has_bundle: sp.has_bundle === "1",
                }}
              />
            </aside>

            <div>
              {services && services.results.length > 0 ? (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {services.results.map((s, i) => (
                      <ScrollReveal key={s.id} delay={0.05 + (i % 6) * 0.04}>
                        <ServiceCard service={s} />
                      </ScrollReveal>
                    ))}
                  </div>
                  {services.next && (
                    <div className="mt-12 text-center">
                      <Link
                        href={appendCursor(services.next, listQs)}
                        className="inline-flex items-center gap-2 uppercase tracking-cap text-xs px-8 py-4 border border-gold/52 text-gold hover:bg-gold hover:text-black transition-colors"
                      >
                        Load more
                      </Link>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-mist text-sm">
                  No services match these filters. Try widening your search.
                </p>
              )}
            </div>
          </div>
        </Container>
      </section>

      {featuredVendors && featuredVendors.results.length > 0 && (
        <section className="section-y">
          <Container>
            <ScrollReveal>
              <SectionHeader
                eyebrow="Featured vendors"
                title="Names you'll keep seeing."
              />
            </ScrollReveal>
            <div className="mt-10 flex gap-4 overflow-x-auto pb-2 -mx-4 px-4 snap-x snap-mandatory">
              {featuredVendors.results.slice(0, 5).map((v) => (
                <Link
                  key={v.id}
                  href={`/services/vendors/${v.slug}`}
                  className="snap-start flex-shrink-0 w-[260px] bg-deep border border-gold/14 hover:border-gold/35 p-6 transition-colors group"
                >
                  <VendorChip vendor={v} />
                  <p className="text-mist text-sm mt-4 line-clamp-2">
                    {v.tagline || v.about || "Local vendor."}
                  </p>
                  <span className="block mt-5 text-[11px] uppercase tracking-luxe text-gold group-hover:translate-x-1 transition-transform">
                    See profile
                  </span>
                </Link>
              ))}
            </div>
          </Container>
        </section>
      )}
    </>
  );
}

function appendCursor(nextUrl: string, base: URLSearchParams): string {
  try {
    const u = new URL(nextUrl, "http://x");
    const next = u.searchParams.get("cursor");
    const out = new URLSearchParams(base);
    if (next) out.set("cursor", next);
    return `/services?${out.toString()}`;
  } catch {
    return "/services";
  }
}
